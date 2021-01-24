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
    public Text score_text;
    public Text rank_text;
    [HideInInspector]
    public bool battle_pause;
    [HideInInspector]
    public int field_id;
    [HideInInspector] public string ip;
    string train_name;
    bool update_done_info=false;

    EnvironmentParameters m_ResetParams;

    GameObject[] actor_objs=new GameObject[4];
    int team1_score=0;
    int team2_score=0;
    Actor actor_info1;
    Actor actor_info2;
    
    public bool battle_done;
    bool is_trainning=true;
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

    public void update_train_info(float win_rate, float reward, float battle_time){
        if (update_done_info==false){
            update_done_info=true;
            StartCoroutine(update_train_info_thread(win_rate, reward, battle_time));
        }
    }

    IEnumerator update_train_info_thread(float win_rate, float reward, float battle_time){
        List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
        formData.Add(new MultipartFormDataSection("train_actor",train_name));
        formData.Add(new MultipartFormDataSection("win_rate",win_rate.ToString()));
        formData.Add(new MultipartFormDataSection("reward",reward.ToString()));
        formData.Add(new MultipartFormDataSection("battle_time",battle_time.ToString()));
        UnityWebRequest www = UnityWebRequest.Post("http://"+ip+":8001/done_train", formData);
        yield return www.SendWebRequest();
    }

    IEnumerator ShowBattleResult(string win_actor, string lose_actor)
    {
        List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
        formData.Add(new MultipartFormDataSection("win",win_actor));
        formData.Add(new MultipartFormDataSection("lose",lose_actor));
        UnityWebRequest www = UnityWebRequest.Post("http://"+ip+":8001/update_actor_stats", formData);
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
        battle_pause=false;
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
    }

    void update_score_board(){
        if (score_text!=null){
            string data_info = String.Format("<color=#{0}>{1} ({3})    {2}</color>", actor_info1.color, actor_info1.name, team1_score,actor_info1.elo); 
            data_info = data_info+"    vs    ";
            data_info = data_info+String.Format("<color=#{0}>{2}    ({3}) {1}</color>", actor_info2.color, actor_info2.name, team2_score,actor_info2.elo); 
            score_text.text = data_info;
        }
    }

    IEnumerator update_rank(){
        List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
        UnityWebRequest www = UnityWebRequest.Post("http://"+ip+":8001/get_actor_list_str", formData);
        yield return www.SendWebRequest();
        if (www.isNetworkError || www.isHttpError){
            Debug.Log("NetworkError");
            yield break;
        }
        string full_re=www.downloadHandler.text;
        if (full_re==""){
            yield break;
        }
        
        string[] items = full_re.Split(',');
        string actor_info_str_all="";
        for (int i=0; i<items.Length; i++){
            if (items[i]==""){
                break;
            }
            string[] info_items = items[i].Split(' ');
            string name=info_items[0];
            string color=info_items[1];
            string elo=info_items[2];
            string actor_inf_str = String.Format("<color=#{0}>{3} {1} {2}</color>", color, name, elo, i+1); 
            actor_info_str_all=actor_info_str_all+actor_inf_str+"\n";
        }
        rank_text.text=actor_info_str_all;
    }

    string get_actor_info_string(Actor actor_info){
        string actor_inf_str = String.Format("<color=#{0}>{1}</color>  天梯分数:{2} ", actor_info.color, actor_info.name, actor_info.elo); 
        return actor_inf_str;
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
        }else{
            foreach (var ps in playerStates)
            {
                if (ps.agentScript.team == scoredTeam)
                {
                    ps.agentScript.AddReward(1 + ps.agentScript.timePenalty);
                    ps.agentScript.win_count=ps.agentScript.win_count+1;
                    ps.agentScript.total_rewards=ps.agentScript.total_rewards+ps.agentScript.m_Reward;
                }
                else
                {
                    ps.agentScript.AddReward(-1);
                }
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
        if (is_trainning==false){
            player_fab.MaxStep=1000;
        }else{
            player_fab.MaxStep=3000;
        }
        
        player_fab.area=this;
        player_fab.speed=actor_info.speed;
        player_fab.power=actor_info.force;
        player_fab.team=team;
        RayPerceptionSensorComponent3D ray_sensor=fab.GetComponent<RayPerceptionSensorComponent3D>();
        ray_sensor.RaysPerDirection=actor_info.ray_count;
        ray_sensor.RayLength=actor_info.ray_range;
        ray_sensor.MaxRayDegrees=180;
        List<string> temp_tags = ray_sensor.DetectableTags;
        BehaviorParameters bp = fab.GetComponent<BehaviorParameters>();
        if (player_fab.team==AgentSoccer.Team.One){
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
        Vector3 new_posi = posi;
        new_posi.y=actor_info.size/2;
        GameObject obj = Instantiate(fab, parent.position+new_posi, Quaternion.identity);
        Transform trans = obj.transform;
        obj.transform.localScale=new Vector3(actor_info.size, actor_info.size, actor_info.size);
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

    public void StartTrains(Actor actor1, Actor actor2, string train_actor_name){
        is_trainning=true;
        update_done_info=false;
        train_name=train_actor_name;
        playerStates.Clear();
        destroy_all();
        actor_objs[0] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0.5f,1.2f), false);
        actor_objs[1] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0.5f,-1.2f), false);
        actor_objs[2] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0.5f,1.2f), false);
        actor_objs[3] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0.5f,-1.2f), false);
    }

    public void StartBattles(Actor actor1, Actor actor2){
        StartCoroutine(update_rank());
        battle_done=false;
        team1_score=0;
        team2_score=0;
        is_trainning=false;
        playerStates.Clear();
        destroy_all();
        actor_objs[0] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,1.2f), true);
        actor_objs[1] = generate_actor_object(actor1, AgentSoccer.Team.One, transform, new Vector3(0f,0f,-1.2f), true);
        actor_objs[2] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,1.2f), true);
        actor_objs[3] = generate_actor_object(actor2, AgentSoccer.Team.Two, transform, new Vector3(0f,0f,-1.2f), true);
        for (int i=0; i<actor_objs.Length; i++){
            if (actor_objs[i]==null){
                destroy_all();
                return;
            }
        }
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
