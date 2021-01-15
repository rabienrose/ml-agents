from mlagents_envs.environment import UnityEnvironment
import time
import numpy as np
# This is a non-blocking call that only loads the environment.
env = UnityEnvironment(file_name=None, seed=1, side_channels=[])
# Start interacting with the environment.
env.reset()
for item in env.behavior_specs:
    print(env.behavior_specs[item])
count=0
while True:
    action=np.array([[count]])
    # env.set_actions("chamo?team=0", action)
    env.step()
    decision_steps, terminal_steps = env.get_steps("chamo?team=0")
    print(decision_steps.agent_id)
    count=count+1
    time.sleep(1)
