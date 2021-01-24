using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Policies;

public class AgentSoccer : Agent
{
    // Note that that the detectable tags are different for the blue and purple teams. The order is
    // * ball
    // * own goal
    // * opposing goal
    // * wall
    // * own teammate
    // * opposing player
    public enum Team
    {
        One = 0,
        Two = 1
    }

    public enum Position
    {
        Striker,
        Goalie,
        Generic
    }

    [HideInInspector]
    public Team team;
    float m_KickPower;
    int m_PlayerIndex;
    public SoccerFieldArea area;
    // The coefficient for the reward for colliding with a ball. Set using curriculum.
    public float m_BallTouch;
    public Position position;

    const float k_Power = 2000f;
    public float power = 1f;
    public float speed = 1f;
    float m_Existential;
    float m_LateralSpeed;
    float m_ForwardSpeed;

    [HideInInspector]
    public float timePenalty;

    [HideInInspector]
    public Rigidbody agentRb;
    BehaviorParameters m_BehaviorParameters;
    Vector3 m_Transform;

    public int win_count=0;
    public int total_match_count=0;
    public float total_rewards=0f;

    EnvironmentParameters m_ResetParams;

    public override void Initialize()
    {
        win_count=0;
        total_match_count=0;
        total_rewards=0f;
        m_Existential = 1f / MaxStep;
        m_BehaviorParameters = gameObject.GetComponent<BehaviorParameters>();
        if (team == Team.One)
        //if (m_BehaviorParameters.TeamId == (int)Team.One)
        {
            // team = Team.One;
            m_Transform = new Vector3(transform.position.x - 4f, transform.position.y, transform.position.z);
        }
        else
        {
            // team = Team.Two;
            m_Transform = new Vector3(transform.position.x + 4f, transform.position.y, transform.position.z);
        }
        if (position == Position.Goalie)
        {
            m_LateralSpeed = 1.0f*speed;
            m_ForwardSpeed = 1.0f*speed;
        }
        else if (position == Position.Striker)
        {
            m_LateralSpeed = 0.3f*speed;
            m_ForwardSpeed = 1.3f*speed;
        }
        else
        {
            m_LateralSpeed = 0.3f*speed;
            m_ForwardSpeed = 1.0f*speed;
        }
        agentRb = GetComponent<Rigidbody>();
        agentRb.maxAngularVelocity = 500;

        var playerState = new PlayerState
        {
            agentRb = agentRb,
            startingPos = transform.position,
            agentScript = this,
        };
        area.playerStates.Add(playerState);
        m_PlayerIndex = area.playerStates.IndexOf(playerState);
        playerState.playerIndex = m_PlayerIndex;

        m_ResetParams = Academy.Instance.EnvironmentParameters;
    }

    public void MoveAgent(ActionSegment<int> act)
    {
        var dirToGo = Vector3.zero;
        var rotateDir = Vector3.zero;

        m_KickPower = 0f;

        var forwardAxis = act[0];
        var rightAxis = act[1];
        var rotateAxis = act[2];

        switch (forwardAxis)
        {
            case 1:
                dirToGo = transform.forward * m_ForwardSpeed;
                m_KickPower = 1f;
                break;
            case 2:
                dirToGo = transform.forward * -m_ForwardSpeed;
                break;
        }

        switch (rightAxis)
        {
            case 1:
                dirToGo = transform.right * m_LateralSpeed;
                break;
            case 2:
                dirToGo = transform.right * -m_LateralSpeed;
                break;
        }

        switch (rotateAxis)
        {
            case 1:
                rotateDir = transform.up * -1f;
                break;
            case 2:
                rotateDir = transform.up * 1f;
                break;
        }

        transform.Rotate(rotateDir, Time.deltaTime * 100f);
        agentRb.AddForce(dirToGo * 2,
            ForceMode.VelocityChange);
    }

    public override void OnActionReceived(ActionBuffers actionBuffers)

    {

        if (position == Position.Goalie)
        {
            // Existential bonus for Goalies.
            AddReward(m_Existential);
        }
        else if (position == Position.Striker)
        {
            // Existential penalty for Strikers
            AddReward(-m_Existential);
        }
        else
        {
            // Existential penalty cumulant for Generic
            timePenalty -= m_Existential;
        }
        MoveAgent(actionBuffers.DiscreteActions);
    }

    public override void Heuristic(in ActionBuffers actionsOut)
    {
        var discreteActionsOut = actionsOut.DiscreteActions;
        discreteActionsOut.Clear();
        //forward
        if (Input.GetKey(KeyCode.W))
        {
            discreteActionsOut[0] = 1;
        }
        if (Input.GetKey(KeyCode.S))
        {
            discreteActionsOut[0] = 2;
        }
        //rotate
        if (Input.GetKey(KeyCode.A))
        {
            discreteActionsOut[2] = 1;
        }
        if (Input.GetKey(KeyCode.D))
        {
            discreteActionsOut[2] = 2;
        }
        //right
        if (Input.GetKey(KeyCode.E))
        {
            discreteActionsOut[1] = 1;
        }
        if (Input.GetKey(KeyCode.Q))
        {
            discreteActionsOut[1] = 2;
        }
    }
    /// <summary>
    /// Used to provide a "kick" to the ball.
    /// </summary>
    void OnCollisionEnter(Collision c)
    {
        var force = k_Power * m_KickPower*power;
        if (position == Position.Goalie)
        {
            force = k_Power*power;
        }
        if (c.gameObject.CompareTag("ball"))
        {
            AddReward(.2f * m_BallTouch);
            var dir = c.contacts[0].point - transform.position;
            dir = dir.normalized;
            c.gameObject.GetComponent<Rigidbody>().AddForce(dir * force);
        }
    }

    public override void OnEpisodeBegin()
    {
        total_match_count=total_match_count+1;
        if(cul_steps>25000 || area.battle_done){
            gameObject.SetActive(false);
            if (m_BehaviorParameters.Model==null){
                float win_rate=(float)win_count/(float)total_match_count;
                float reward=(float)total_rewards/(float)total_match_count;
                float battle_time=25000f/(float)total_match_count*0.02f;
                area.update_train_info(win_rate, reward, battle_time);
            }
        }
        timePenalty = 0;
        m_BallTouch = m_ResetParams.GetWithDefault("ball_touch", 0);
        if (team == Team.One)
        {
            transform.rotation = Quaternion.Euler(0f, 90f, 0f);
        }
        else
        {
            transform.rotation = Quaternion.Euler(0f, -90f, 0f);
        }
        transform.position = m_Transform;
        agentRb.velocity = Vector3.zero;
        agentRb.angularVelocity = Vector3.zero;
        SetResetParameters();
        
    }

    public void StopAction(bool stop){
        DecisionRequester d=GetComponent<DecisionRequester>();
        d.bStop=stop;
    }

    public void SetResetParameters()
    {
        area.ResetBall();
    }
}
