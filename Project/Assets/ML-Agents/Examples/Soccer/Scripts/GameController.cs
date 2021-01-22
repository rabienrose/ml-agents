using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.Rendering;
using UnityEngine.Serialization;
using Unity.MLAgents.Policies;
using Unity.Barracuda;
using Unity.Barracuda.ONNX;
using System.Text;
using System.IO;

public class Actor{
    public string name="";
    public float speed=0;
    public string color="";
    public float ray_range=0;
    public int ray_count=0;
    public float force=0;
    public float size=0;
    public float mass=0;
    public int win_count=0;
    public int lose_count=0;
    public NNModel model=null;
    public string dump(){
        string re_str ="name ";
        re_str=re_str+speed+" ";
        re_str=re_str+color+" ";
        re_str=re_str+ray_range+" ";
        re_str=re_str+ray_count+" ";
        re_str=re_str+force+" ";
        re_str=re_str+size+" ";
        re_str=re_str+mass;
        return re_str;
    }
}

public class GameController : MonoBehaviour{
    public AgentSoccer actor_agent;
    public SoccerFieldArea[] fields;
    //string oss_model_folder="https://monster-war.oss-cn-beijing-internal.aliyuncs.com/model";
    string oss_model_folder="https://monster-war.oss-cn-beijing.aliyuncs.com/model";
    int field_to_use=5;
    bool train_mode=false;
    int train_count=0;

    protected void Start(){
        if (field_to_use>fields.Length){
            field_to_use=fields.Length;
        }
        if (train_mode){
            
        }else{
            field_to_use=1;
        }
        StartCoroutine(Loop());
        
    }

    Actor parse_actor(string info_str){
        string[] items = info_str.Split(' ');
        Actor actor= new Actor();
        actor.name=items[0];
        actor.speed=float.Parse(items[1]);
        actor.color=items[2];
        actor.ray_range=float.Parse(items[3]);
        actor.ray_count=Int32.Parse(items[4]);
        actor.force=float.Parse(items[5]);
        actor.size=float.Parse(items[6]);
        actor.mass=float.Parse(items[7]);
        actor.win_count=Int32.Parse(items[8]);
        actor.lose_count=Int32.Parse(items[9]);
        return actor;
    }

    IEnumerator DownloadModel(string model_name, Actor actor)
    {
        if (model_name!=""){
            String model_url=oss_model_folder+"/"+model_name;
            Debug.Log(model_url);
            UnityWebRequest www = UnityWebRequest.Get(model_url);
            yield return www.SendWebRequest();
            if(www.isNetworkError || www.isHttpError) {
                Debug.Log("download model wrong!!!");
                yield break;
            }
            byte[] results = www.downloadHandler.data;
            actor.model = LoadOnnxModel(results);
        }
    }

    SoccerFieldArea get_idle_field(){
        for (int i=0; i<field_to_use; i++){
            if(fields[i].CheckFieldIdle()){
                return fields[i];
            }
        }
        return null;
    }

    NNModel LoadOnnxModel(byte[] rawModel)
    {
        var converter = new ONNXModelConverter(true);
        var onnxModel = converter.Convert(rawModel);

        NNModelData assetData = ScriptableObject.CreateInstance<NNModelData>();
        using (var memoryStream = new MemoryStream())
        using (var writer = new BinaryWriter(memoryStream))
        {
            ModelWriter.Save(writer, onnxModel);
            assetData.Value = memoryStream.ToArray();
        }
        assetData.name = "Data";
        assetData.hideFlags = HideFlags.HideInHierarchy;

        var asset = ScriptableObject.CreateInstance<NNModel>();
        asset.modelData = assetData;
        return asset;
    }

    IEnumerator Loop(){
        System.Random rnd = new System.Random();
        
        for(int i=0; i<field_to_use; i++){
            fields[i].gameObject.SetActive(true);
            fields[i].field_id=i;
        }
        while (true){
            SoccerFieldArea idle_field = get_idle_field();
            if (idle_field==null){
                yield return new WaitForSeconds(1);
                continue;
            }
            
            List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
            UnityWebRequest www;
            if (train_mode){
                www = UnityWebRequest.Post("http://39.105.230.163:8001/pop_train_quene", formData);
            }else{
                www = UnityWebRequest.Post("http://39.105.230.163:8001/pop_battle_quene", formData);
            }
            
            yield return www.SendWebRequest();
            if (www.isNetworkError || www.isHttpError){
                Debug.Log("NetworkError");
                yield return new WaitForSeconds(100);
                continue;
            }
            string full_re=www.downloadHandler.text;
            if (full_re==""){
                yield return new WaitForSeconds(100);
                continue;
            }
            string[] items = full_re.Split(',');
            if (items.Length==1){
                yield return new WaitForSeconds(10);
                continue;
            }
            Actor actor1 = parse_actor(items[0]);
            Actor actor2 = parse_actor(items[1]);
            string model1_name=items[2];
            string model2_name=items[3];
            yield return StartCoroutine(DownloadModel(model1_name, actor1));
            yield return StartCoroutine(DownloadModel(model2_name, actor2));         
            Debug.Log("reset field: "+idle_field.field_id+", "+actor1.model+", "+actor2.model);
            if (train_mode==false){
                idle_field.StartBattles(actor1, actor2);
            }else{
                int dice = rnd.Next(0, 2);
                train_count=train_count+1;
                if (dice==0){
                    idle_field.StartTrains(actor1, actor2);
                }else{
                    idle_field.StartTrains(actor2, actor1);
                }
            }
            yield return new WaitForSeconds(1);
        }
    }
}