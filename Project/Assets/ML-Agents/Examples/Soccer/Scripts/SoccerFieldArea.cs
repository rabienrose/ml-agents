using System.Collections;
using System.Collections.Generic;
using Unity.MLAgents;
using UnityEngine;
using UnityEngine.Serialization;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Policies;
using Unity.MLAgents.Sensors;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Text;
using System.IO;
using System;
[System.Serializable]
public class PlayerState
{
    public int playerIndex;
    [FormerlySerializedAs("agentRB")]
    public Rigidbody agentRb;
    public Vector3 startingPos;
    public AgentSoccer agentScript;
    public float ballPosReward;
}

public class SoccerFieldArea : MonoBehaviour
{
    public GameObject ball;
    public AgentSoccer player_fab;
    [FormerlySerializedAs("ballRB")]
    [HideInInspector]
    public Rigidbody ballRb;
    public GameObject ground;
    public GameObject centerPitch;
    SoccerBallController m_BallController;
    public List<PlayerState> playerStates = new List<PlayerState>();
    [HideInInspector]
    public Vector3 ballStartingPos;
    public Text score1_text;
    public Text score2_text;
    [HideInInspector]
    public bool battle_pause;

    EnvironmentParameters m_ResetParams;

    GameObject[] actor_objs=new GameObject[4];
    int team1_score=0;
    int team2_score=0;
    Actor actor_info1;
    Actor actor_info2;
    public bool battle_done;
    bool is_trainning=true;
    public int max_battle_count=100;
    void Awake()
    {
        battle_done=false;
        battle_pause = false;
        ballRb = ball.GetComponent<Rigidbody>();
        m_BallController = ball.GetComponent<SoccerBallController>();
        m_BallController.area = this;
        ballStartingPos = ball.transform.position;
        m_ResetParams = Academy.Instance.EnvironmentParameters;
    }

    IEnumerator ShowBattleResult(string win_actor, string lose_actor)
    {
        List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
        formData.Add(new MultipartFormDataSection("win",win_actor));
        formData.Add(new MultipartFormDataSection("lose",lose_actor));
        UnityWebRequest www = UnityWebRequest.Post("http://0.0.0.0:8001/update_actor_stats", formData);
        yield return www.SendWebRequest();
    }

    IEnumerator DoneMatch()
    {
        if (!is_trainning){
            yield return new WaitForSeconds(2);
        }

        foreach (var ps in playerStates)
        {
            ps.agentScript.EndEpisode();  //all agents need to be reset
        }
    }

    IEnumerator FreezeActors()
    {
        foreach (var ps in playerStates)
        {
            ps.agentScript.StopAction(true);
        }
        yield return new WaitForSeconds(3);
        foreach (var ps in playerStates)
        {
            ps.agentScript.StopAction(false);
        }
        battle_pause=false;
    }

    void update_score_board(){
        if (score1_text!=null &&score2_text!=null){
            string data_info = String.Format("<color=#{0}>{1}    {2}</color>", actor_info1.color, actor_info1.name, team1_score); 
            score1_text.text = data_info;
            data_info = String.Format("<color=#{0}>{2}    {1}</color>", actor_info2.color, actor_info2.name, team2_score); 
            score2_text.text = data_info;
        }
    }

    public void GoalTouched(AgentSoccer.Team scoredTeam)
    {
        if (battle_pause){
            return;
        }
        battle_pause=true;
        if (is_trainning==false){
            if (scoredTeam==AgentSoccer.Team.One){
                team1_score=team1_score+1;
            }else{
                team2_score=team2_score+1;
            }
            if (team1_score>=10)
            {
                battle_done=true;
                StartCoroutine(ShowBattleResult(actor_info1.name, actor_info2.name));
            }
            if (team2_score>=10)
            {
                battle_done=true;
                StartCoroutine(ShowBattleResult(actor_info2.name, actor_info1.name));
            }
            update_score_board();
            StartCoroutine(FreezeActors());
        }
        foreach (var ps in playerStates)
        {
            if (ps.agentScript.team == scoredTeam)
            {
                ps.agentScript.AddReward(1 + ps.agentScript.timePenalty);
            }
            else
            {
                ps.agentScript.AddReward(-1);
            }
        }
        StartCoroutine(DoneMatch());
    }

    public void ResetBall()
    {
        ball.transform.position = ballStartingPos;
        ballRb.velocity = Vector3.zero;
        ballRb.angularVelocity = Vector3.zero;

        var ballScale = m_ResetParams.GetWithDefault("ball_scale", 0.015f);
        ballRb.transform.localScale = new Vector3(ballScale, ballScale, ballScale);
    }

    public bool CheckFieldIdle(){
        bool all_deactive=true;
        for (int i=0;i<actor_objs.Length; i++){
            if(actor_objs[i]!=null && actor_objs[i].activeSelf){
                all_deactive=false;
            }
        }
        return all_deactive;
    }

    GameObject generate_actor_object(Actor actor_info, AgentSoccer.Team team, Transform parent, Vector3 posi, bool battle){
        if (actor_info.model==null && battle==true){
            return null;
        }
        GameObject fab=player_fab.gameObject;
        AgentSoccer agent=fab.GetComponent<AgentSoccer>();
        agent.battle_count=max_battle_count;
        agent.area=this;
        agent.speed=actor_info.speed;
        agent.power=actor_info.force;
        agent.team=team;
        RayPerceptionSensorComponent3D ray_sensor=fab.GetComponent<RayPerceptionSensorComponent3D>();
        ray_sensor.RaysPerDirection=actor_info.ray_count;
        ray_sensor.RayLength=actor_info.ray_range;
        ray_sensor.MaxRayDegrees=180;
        List<string> temp_tags = ray_sensor.DetectableTags;
        BehaviorParameters bp = fab.GetComponent<BehaviorParameters>();
        if (agent.team==AgentSoccer.Team.One){
            temp_tags[1]="Goal1";
            temp_tags[2]="Goal2";
            temp_tags[4]="Agent1";
            temp_tags[5]="Agent2";
            fab.tag = "Agent1";
            bp.TeamId=0;
        }else{
            temp_tags[1]="Goal2";
            temp_tags[2]="Goal1";
            temp_tags[4]="Agent2";
            temp_tags[5]="Agent1";
            fab.tag = "Agent2";
            bp.TeamId=0;
        }
        ray_sensor.DetectableTags=temp_tags;
        
        bp.BehaviorName=actor_info.name;
        if (actor_info.model!=null){
            bp.Model=actor_info.model;
            bp.BehaviorType=BehaviorType.InferenceOnly;
        }else{
            bp.Model=null;
            bp.BehaviorType=BehaviorType.Default;
        }
        
        GameObject obj = Instantiate(fab, parent.position+posi, Quaternion.identity);
        Transform trans = obj.transform;
        trans.SetParent(parent);
        Transform childTrans = trans.Find("AgentCube");
        Material myMaterial = childTrans.gameObject.GetComponent<Renderer>().material;
        myMaterial.color = getColorFromString(actor_info.color);
        return obj;
    }

    Color getColorFromString(string color_string){
        string r_str=color_string.Substring(0,2);
        string g_str=color_string.Substring(2,2);
        string b_str=color_string.Substring(4,2);
        Color color= new Color();
        color.r = int.Parse(r_str, System.Globalization.NumberStyles.HexNumber)/255f;
        color.g = int.Parse(g_str, System.Globalization.NumberStyles.HexNumber)/255f;
        color.b = int.Parse(b_str, System.Globalization.NumberStyles.HexNumber)/255f;
        return color;
    
    }

    void destroy_all(){
        for (int i=0;i<actor_objs.Length; i++){
            if(actor_objs[i]!=null){
                Destroy(actor_objs[i]);
                actor_objs[i]=null;
            }
        }
    }

    public void StartTrains(Actor actor1, Actor actor2){
        is_trainning=true;
        playerStates.Clear();
        destroy_all();
        actor_objs[0] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,3f), false);
        actor_objs[1] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,-3f), false);
        actor_objs[2] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,3f), false);
        actor_objs[3] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,-3f), false);
    }

    public void StartBattles(Actor actor1, Actor actor2){
        is_trainning=false;
        playerStates.Clear();
        destroy_all();
        actor_objs[0] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,3f), true);
        actor_objs[1] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,-3f), true);
        actor_objs[2] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,3f), true);
        actor_objs[3] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,-3f), true);
        for (int i=0; i<actor_objs.Length; i++){
            if (actor_objs[i]==null){
                destroy_all();
                return;
            }
        }
        battle_done=false;
        actor_info1=actor1;
        actor_info2=actor2;
        Transform goal1Trans = transform.Find("Field").Find("Goal1");
        Material myMaterial1 = goal1Trans.gameObject.GetComponent<Renderer>().material;
        myMaterial1.color = getColorFromString(actor1.color);
        Transform goal2Trans = transform.Find("Field").Find("Goal2");
        Material myMaterial2 = goal2Trans.gameObject.GetComponent<Renderer>().material;
        myMaterial2.color = getColorFromString(actor2.color);
        update_score_board();
    }
}
