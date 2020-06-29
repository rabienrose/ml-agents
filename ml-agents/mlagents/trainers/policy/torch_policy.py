from typing import Any, Dict, List
import numpy as np
import torch
import os
from torch import onnx
from mlagents.trainers.action_info import ActionInfo
from mlagents.trainers.brain_conversion_utils import get_global_agent_id

from mlagents.trainers.policy import Policy
from mlagents_envs.base_env import DecisionSteps
from mlagents.tf_utils import tf
from mlagents_envs.timers import timed

from mlagents.trainers.policy.policy import UnityPolicyException
from mlagents.trainers.settings import TrainerSettings
from mlagents.trainers.trajectory import SplitObservations
from mlagents.trainers.brain import BrainParameters
from mlagents.trainers.models_torch import ActorCritic

EPSILON = 1e-7  # Small value to avoid divide by zero


class TorchPolicy(Policy):
    def __init__(
        self,
        seed: int,
        brain: BrainParameters,
        trainer_settings: TrainerSettings,
        model_path: str,
        load: bool,
        tanh_squash: bool = False,
        reparameterize: bool = False,
        condition_sigma_on_obs: bool = True,
    ):
        """
        Policy that uses a multilayer perceptron to map the observations to actions. Could
        also use a CNN to encode visual input prior to the MLP. Supports discrete and
        continuous action spaces, as well as recurrent networks.
        :param seed: Random seed.
        :param brain: Assigned BrainParameters object.
        :param trainer_settings: Defined training parameters.
        :param load: Whether a pre-trained model will be loaded or a new one created.
        :param tanh_squash: Whether to use a tanh function on the continuous output,
        or a clipped output.
        :param reparameterize: Whether we are using the resampling trick to update the policy
        in continuous output.
        """
        super(TorchPolicy, self).__init__(brain, seed, trainer_settings)
        self.grads = None
        num_layers = trainer_settings.network_settings.num_layers
        self.h_size = trainer_settings.network_settings.hidden_units
        self.seed = seed
        self.brain = brain
        self.global_step = 0
        self.m_size = 0
        self.model_path = model_path

        self.act_size = brain.vector_action_space_size
        self.act_type = brain.vector_action_space_type
        self.sequence_length = 1
        if trainer_settings.network_settings.memory is not None:
            self.m_size = trainer_settings.network_settings.memory.memory_size
            self.sequence_length = (
                trainer_settings.network_settings.memory.sequence_length
            )
            if self.m_size == 0:
                raise UnityPolicyException(
                    "The memory size for brain {0} is 0 even "
                    "though the trainer uses recurrent.".format(brain.brain_name)
                )
            elif self.m_size % 2 != 0:
                raise UnityPolicyException(
                    "The memory size for brain {0} is {1} "
                    "but it must be divisible by 2.".format(
                        brain.brain_name, self.m_size
                    )
                )
        else:
            self.m_size = 0
            self.sequence_length = 1
        if num_layers < 1:
            num_layers = 1
        self.num_layers = num_layers
        self.vis_encode_type = trainer_settings.network_settings.vis_encode_type
        self.tanh_squash = tanh_squash
        self.reparameterize = reparameterize
        self.condition_sigma_on_obs = condition_sigma_on_obs

        # Non-exposed parameters; these aren't exposed because they don't have a
        # good explanation and usually shouldn't be touched.
        self.log_std_min = -20
        self.log_std_max = 2

        self.inference_dict: Dict[str, tf.Tensor] = {}
        self.update_dict: Dict[str, tf.Tensor] = {}
        # TF defaults to 32-bit, so we use the same here.
        torch.set_default_tensor_type(torch.DoubleTensor)

        reward_signal_configs = trainer_settings.reward_signals
        reward_signal_names = [key.value for key, _ in reward_signal_configs.items()]

        self.stats_name_to_update_name = {
            "Losses/Value Loss": "value_loss",
            "Losses/Policy Loss": "policy_loss",
        }

        self.actor_critic = ActorCritic(
            h_size=int(trainer_settings.network_settings.hidden_units),
            act_type=self.act_type,
            vector_sizes=[brain.vector_observation_space_size],
            act_size=brain.vector_action_space_size,
            normalize=trainer_settings.network_settings.normalize,
            num_layers=int(trainer_settings.network_settings.num_layers),
            m_size=self.m_size,
            use_lstm=self.use_recurrent,
            visual_sizes=brain.camera_resolutions,
            vis_encode_type=trainer_settings.network_settings.vis_encode_type,
            stream_names=reward_signal_names,
            separate_critic=self.use_continuous_act,
        )

    def split_decision_step(self, decision_requests):
        vec_vis_obs = SplitObservations.from_observations(decision_requests.obs)
        mask = None
        if not self.use_continuous_act:
            mask = torch.ones(
                [len(decision_requests), np.sum(self.brain.vector_action_space_size)]
            )
            if decision_requests.action_mask is not None:
                mask = torch.as_tensor(
                    1 - np.concatenate(decision_requests.action_mask, axis=1)
                )
        return vec_vis_obs.vector_observations, vec_vis_obs.visual_observations, mask

    def update_normalization(self, vector_obs: np.ndarray) -> None:
        """
        If this policy normalizes vector observations, this will update the norm values in the graph.
        :param vector_obs: The vector observations to add to the running estimate of the distribution.
        """
        vector_obs = [torch.as_tensor(vector_obs)]
        if self.use_vec_obs and self.normalize:
            self.actor_critic.update_normalization(vector_obs)

    @timed
    def sample_actions(self, vec_obs, vis_obs, masks=None, memories=None, seq_len=1):
        dists, (
            value_heads,
            mean_value,
        ), memories = self.actor_critic.get_dist_and_value(
            vec_obs, vis_obs, masks, memories, seq_len
        )

        actions = self.actor_critic.sample_action(dists)
        log_probs, entropies = self.actor_critic.get_probs_and_entropy(actions, dists)
        if self.act_type == "continuous":
            actions.squeeze_(-1)

        return actions, log_probs, entropies, value_heads, memories

    def evaluate_actions(
        self, vec_obs, vis_obs, actions, masks=None, memories=None, seq_len=1
    ):
        dists, (value_heads, mean_value), _ = self.actor_critic.get_dist_and_value(
            vec_obs, vis_obs, masks, memories, seq_len
        )

        log_probs, entropies = self.actor_critic.get_probs_and_entropy(actions, dists)

        return log_probs, entropies, value_heads

    @timed
    def evaluate(
        self, decision_requests: DecisionSteps, global_agent_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates policy for the agent experiences provided.
        :param global_agent_ids:
        :param decision_requests: DecisionStep object containing inputs.
        :return: Outputs from network as defined by self.inference_dict.
        """
        vec_obs, vis_obs, masks = self.split_decision_step(decision_requests)
        vec_obs = [torch.as_tensor(vec_obs)]
        vis_obs = [torch.as_tensor(vis_ob) for vis_ob in vis_obs]
        memories = torch.as_tensor(self.retrieve_memories(global_agent_ids)).unsqueeze(
            0
        )

        run_out = {}
        with torch.no_grad():
            action, log_probs, entropy, value_heads, memories = self.sample_actions(
                vec_obs, vis_obs, masks=masks, memories=memories
            )
        run_out["action"] = action.detach().numpy()
        run_out["pre_action"] = action.detach().numpy()
        # Todo - make pre_action difference
        run_out["log_probs"] = log_probs.detach().numpy()
        run_out["entropy"] = entropy.detach().numpy()
        run_out["value_heads"] = {
            name: t.detach().numpy() for name, t in value_heads.items()
        }
        run_out["value"] = np.mean(list(run_out["value_heads"].values()), 0)
        run_out["learning_rate"] = 0.0
        if self.use_recurrent:
            run_out["memories"] = memories.detach().numpy()
        self.actor_critic.update_normalization(vec_obs)
        return run_out

    def get_action(
        self, decision_requests: DecisionSteps, worker_id: int = 0
    ) -> ActionInfo:
        """
        Decides actions given observations information, and takes them in environment.
        :param worker_id:
        :param decision_requests: A dictionary of brain names and BrainInfo from environment.
        :return: an ActionInfo containing action, memories, values and an object
        to be passed to add experiences
        """
        if len(decision_requests) == 0:
            return ActionInfo.empty()

        global_agent_ids = [
            get_global_agent_id(worker_id, int(agent_id))
            for agent_id in decision_requests.agent_id
        ]  # For 1-D array, the iterator order is correct.

        run_out = self.evaluate(
            decision_requests, global_agent_ids
        )  # pylint: disable=assignment-from-no-return
        self.save_memories(global_agent_ids, run_out.get("memory_out"))
        return ActionInfo(
            action=run_out.get("action"),
            value=run_out.get("value"),
            outputs=run_out,
            agent_ids=list(decision_requests.agent_id),
        )

    def save_model(self, step=0):
        """
        Saves the model
        :param step: The number of steps the model was trained for
        """
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
        save_path = self.model_path + "/model-" + str(step) + ".pt"
        torch.save(self.actor_critic.state_dict(), save_path)

    def load_model(self, step=0):
        load_path = self.model_path + "/model-" + str(step) + ".pt"
        self.actor_critic.load_state_dict(torch.load(load_path))

    def export_model(self, step=0):
        fake_vec_obs = [torch.zeros([1] + [self.brain.vector_observation_space_size])]
        fake_vis_obs = [torch.zeros([1] + [84, 84, 3])]
        fake_masks = torch.ones([1] + self.actor_critic.act_size)
        fake_memories = torch.zeros([1] + [self.m_size])
        export_path = "./model-" + str(step) + ".onnx"
        output_names = ["action", "action_probs"]
        input_names = ["vector_observation", "action_mask"]
        dynamic_axes = {"vector_observation": [0], "action": [0], "action_probs": [0]}
        onnx.export(
            self.actor_critic,
            (fake_vec_obs, fake_vis_obs, fake_masks),
            export_path,
            verbose=True,
            opset_version=12,
            input_names=input_names,
            output_names=output_names,
            dynamic_axes=dynamic_axes,
        )

    @property
    def vis_obs_size(self):
        return self.brain.number_visual_observations

    @property
    def vec_obs_size(self):
        return self.brain.vector_observation_space_size

    @property
    def use_vis_obs(self):
        return self.vis_obs_size > 0

    @property
    def use_vec_obs(self):
        return self.vec_obs_size > 0

    def get_current_step(self):
        """
        Gets current model step.
        :return: current model step.
        """
        step = self.global_step
        return step

    def increment_step(self, n_steps):
        """
        Increments model step.
        """
        self.global_step += n_steps
        return self.get_current_step()