using UnityEngine;

public class SoccerBallController : MonoBehaviour
{
    [HideInInspector]
    public SoccerFieldArea area;
    string Goal2Tag="Goal2"; //will be used to check if collided with purple goal
    string Goal1Tag="Goal1"; //will be used to check if collided with blue goal

    void OnCollisionEnter(Collision col)
    {
        if (col.gameObject.CompareTag(Goal2Tag)) //ball touched purple goal
        {
            area.GoalTouched(AgentSoccer.Team.One);
        }
        if (col.gameObject.CompareTag(Goal1Tag)) //ball touched blue goal
        {
            area.GoalTouched(AgentSoccer.Team.Two);
        }
    }
}
