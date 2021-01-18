import requests
import os
import pymongo
import oss2
import numpy as np
from common.config import get_config
import random
import time
import json
import time
from datetime import datetime
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from random import randint
[bucket, myclient]=get_config()
app = Flask(__name__)
mydb=myclient["b_live"]
user_table = mydb["user"]
actor_table = mydb["actor"]
train_table = mydb["train"]
battle_table = mydb["battle"]

@app.route('/get_actor_list', methods=['GET', 'POST'])
def get_actor_list():
    actor_list = list(actor_table.find({},{"_id":0}))
    return json.dumps(actor_list)

@app.route('/update_actor_stats', methods=['GET', 'POST'])
def update_actor_stats():
    win_actor=request.form['win']
    lose_actor=request.form['lose']
    win_count=-1
    for x in actor_table.find({"name":win_actor},{"win_count":1,"_id":0}):
        win_count=x["win_count"]
    lose_count=-1
    for x in actor_table.find({"name":lose_actor},{"lose_count":1,"_id":0}):
        lose_count=x["lose_count"]
    if win_count>=0 and lose_count>=0:
        actor_table.update_one({"name":win_actor},{"$set":{"win_count":win_count+1}})
        actor_table.update_one({"name":lose_actor},{"$set":{"lose_count":lose_count+1}})
    return "ok"


@app.route('/add_actor', methods=['GET', 'POST'])
def add_actor():
    actor_data = request.form['actor_data']
    actor_obj = json.loads(actor_data)
    name=actor_obj['name']
    color=actor_obj['color']
    mass=actor_obj['mass']
    ray_count=actor_obj['ray_count']
    ray_range=actor_obj['ray_range']
    speed=actor_obj['speed']
    force=actor_obj['force']
    size=actor_obj['size']
    existed=False
    for _ in actor_table.find({"name":name}):
        existed=True
    if existed:
        return json.dumps(["existed_name"])
    existed=False
    for _ in actor_table.find({"color":color}):
        existed=True
    if existed:
        return json.dumps(["existed_color"])
    actor_info={"name":name,"color":color,"mass":mass,"ray_count":ray_count, "ray_range":ray_range, "speed":speed, "force":force, "size":size, "train_steps":0, "win_count":0, "lose_count":0}
    actor_table.insert_one(actor_info)
    return json.dumps(["ok"])

@app.route('/del_actor', methods=['GET', 'POST'])
def del_actor():
    pass

def get_actor_info_string(x):
    re_str=""
    re_str=re_str+x["name"]+" "
    re_str=re_str+str(x["speed"])+" "
    re_str=re_str+x["color"]+" "
    re_str=re_str+str(x["ray_range"])+" "
    re_str=re_str+str(x["ray_count"])+" "
    re_str=re_str+str(x["force"])+" "
    re_str=re_str+str(x["size"])+" "
    re_str=re_str+str(x["mass"])+" "
    re_str=re_str+str(x["win_count"])+" "
    re_str=re_str+str(x["lose_count"])
    return re_str

def get_model_name(actor_name, b_rand):
    model_name=""
    onnx_list=[]
    for obj in oss2.ObjectIterator(bucket, prefix="model/"+actor_name):
        str_vec=obj.key.split("/")
        if len(str_vec)==2:
            model_name=str_vec[-1]
            vec_name=model_name.split("-")
            if actor_name==vec_name[0]:
                step=int(vec_name[1].split(".")[0])
                onnx_list.append(step)
    onnx_list.sort(reverse=True)
    count=0
    filtered_models=[]
    for item in onnx_list:
        local_name=actor_name+"-"+str(item)+".onnx"
        if count<=4:
            filtered_models.append(local_name)
        else:
            oss_file_path = "model"+"/"+local_name
            bucket.delete_object(oss_file_path)
        count=count+1
    
    if len(filtered_models)>=1:
        if (b_rand):
            rand_ind = randint(0, len(filtered_models)-1)
        else:
            rand_ind=0
        return filtered_models[rand_ind]
    else:
        return ""

def get_train_info_str(train_info):
    find_actor_b=False
    re_string=""
    for x in actor_table.find({"name":train_info["train_actor"]}):
        info_string = get_actor_info_string(x)
        re_string=re_string+info_string+","
        find_actor_b=True
    if find_actor_b==False:
        return "train_quene_empty"
    find_actor_b=False
    for x in actor_table.find({"name":train_info["target_actor"]}):
        info_string = get_actor_info_string(x)
        re_string=re_string+info_string+","
        find_actor_b=True
    if find_actor_b==False:
        return "train_quene_empty"
    re_string=re_string+","
    re_string=re_string+get_model_name(train_info["target_actor"], True)
    return re_string

@app.route('/pop_train_quene', methods=['GET', 'POST'])
def pop_train_quene():
    train_list = list(train_table.find({}))
    re_string=""
    if len(train_list)>0:
        first_train=train_list[0]
        re_string = get_train_info_str(first_train)
        train_table.delete_one({"_id":first_train["_id"]})
    else:
        actor_list = list(actor_table.find({},{"_id":0,"name":1}))
        rand_ind1 = randint(0, len(actor_list)-1)
        rand_ind2 = randint(0, len(actor_list)-1)
        first_train={"train_actor":actor_list[rand_ind1]["name"], "target_actor":actor_list[rand_ind2]["name"]}
        re_string = get_train_info_str(first_train)
    return re_string

def get_battle_info_str(battle_info):
    re_string=""
    find_actor_b=False
    for x in actor_table.find({"name":battle_info["actor1"]}):
        info_string = get_actor_info_string(x)
        re_string=re_string+info_string+","
        find_actor_b=True
    if find_actor_b==False:
        return "battle_quene_empty"
    find_actor_b=False
    for x in actor_table.find({"name":battle_info["actor2"]}):
        info_string = get_actor_info_string(x)
        re_string=re_string+info_string+","
        find_actor_b=True
    if find_actor_b==False:
        return "battle_quene_empty"
    re_string=re_string+get_model_name(battle_info["actor1"], False)+","
    re_string=re_string+get_model_name(battle_info["actor2"], False)
    return re_string

@app.route('/pop_battle_quene', methods=['GET', 'POST'])
def pop_battle_quene():
    battle_list = list(battle_table.find({}))
    re_string=""
    if len(battle_list)>0:
        first_battle=battle_list[0]
        re_string = get_battle_info_str(first_battle)
        battle_table.delete_one({"_id":first_battle["_id"]})
    else:
        actor_list = list(actor_table.find({},{"_id":0,"name":1}))
        rand_ind1 = randint(0, len(actor_list)-1)
        rand_ind2 = randint(0, len(actor_list)-1)
        first_battle={"actor1":actor_list[rand_ind1]["name"], "actor2":actor_list[rand_ind2]["name"]}
        re_string = get_battle_info_str(first_battle)
    return re_string

@app.route('/add_train_quene', methods=['GET', 'POST'])
def add_train_quene():
    train_data = request.form['train_data']
    train_obj = json.loads(train_data)
    train_actor=train_obj['train_actor']
    target_actor=train_obj['target_actor']
    train_count=train_obj['train_count']
    if actor_table.find({"name":train_actor}).count(True)==0:
        return json.dumps(["train_actor_not_exist"])
    if target_actor!="self" and target_actor!="all":
        if actor_table.find({"name":target_actor}).count(True)==0:
            return json.dumps(["target_actor_not_exist"])
    if target_actor=="self":
        for _ in range(train_count):
            train_table.insert_one({"train_actor":train_actor, "target_actor":train_actor})
    elif target_actor=="all":
        for _ in range(train_count):
            actor_list = list(actor_table.find({},{"_id":0,"name":1}))
            rand_ind = randint(0, len(actor_list)-1)
            train_table.insert_one({"train_actor":train_actor, "target_actor":actor_list[rand_ind]["name"]})
    else:
        for _ in range(train_count):
            train_table.insert_one({"train_actor":train_actor, "target_actor":target_actor})
    return json.dumps(["ok"])

@app.route('/add_battle_quene', methods=['GET', 'POST'])
def add_battle_quene():
    battle_data = request.form['battle_data']
    battle_obj = json.loads(battle_data)
    actor1=battle_obj['actor1']
    actor2=battle_obj['actor2']
    if actor_table.find({"name":actor1}).count(True)==0:
        return json.dumps(["actor1_not_exist"])
    if actor_table.find({"name":actor2}).count(True)==0:
        return json.dumps(["actor2_not_exist"])
    re_string= get_model_name(actor1, False)
    if re_string=="":
        return json.dumps(["actor1_no_model"])
    re_string= get_model_name(actor2, False)
    if re_string=="":
        return json.dumps(["actor2_no_model"])
    battle_table.insert_one({"actor1":actor1, "actor2":actor2})
    battle_table.insert_one({"actor1":actor2, "actor2":actor1})
    return json.dumps(["ok"])

@app.route('/show_battle_qunue', methods=['GET', 'POST'])
def show_battle_qunue():
    battle_list = list(battle_table.find({},{"_id":0}))
    return json.dumps(battle_list)

@app.route('/show_train_qunue', methods=['GET', 'POST'])
def show_train_qunue():
    train_list = list(train_table.find({},{"_id":0}))
    return json.dumps(train_list)

@app.route('/get_train_list', methods=['GET', 'POST'])
def get_train_list():
    pass

@app.route('/get_access_list', methods=['GET', 'POST'])
def get_access_list():
    usr_info=[]
    for x in user_table.find({}):
        usr_info.append(x)
    sorted_score = sorted(usr_info, key=lambda x: x["timestamp"])
    re_list=[]
    count=0
    for i in range(len(sorted_score)-1, -1, -1):
        d=sorted_score[i]
        time_str=datetime.fromtimestamp(d["timestamp"]+3600*8).strftime("%H:%M:%S,%d/%m")
        re_list.append({"name":d["user_name"],"count":d["count"],"time":time_str})
        count=count+1
        if count>40:
            break
    return json.dumps(re_list)

if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'xxx'
    app.config['UPLOAD_FOLDER']='./raw'
    app.debug = False
    app.run('0.0.0.0', port=8001)
