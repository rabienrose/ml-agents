import requests
import os
import pymongo
import oss2
import numpy as np
from common.config import get_config
import random
import time
import json
import math
from datetime import datetime
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from random import randint
from flask import jsonify, abort, make_response
from flask_httpauth import HTTPBasicAuth
[bucket, myclient]=get_config()
app = Flask(__name__)
auth = HTTPBasicAuth()
mydb=myclient["b_live"]
user_table = mydb["user"]
actor_table = mydb["actor"]
battle_table = mydb["battle"]
account_table = mydb["account"]

@app.route('/get_actor_list', methods=['GET', 'POST'])
def get_actor_list():
    actor_list = list(actor_table.find({},{"_id":0}))
    common_actor_infos=[]
    for item in actor_list:
        info={}
        info["name"]=item["name"]
        info["color"]=item["color"]
        info["mass"]=item["mass"]
        info["ray_count"]=item["ray_count"]
        info["ray_range"]=item["ray_range"]
        info["speed"]=item["speed"]
        info["force"]=item["force"]
        info["elo"]=item["elo"]
        common_actor_infos.append(info)
    return json.dumps(common_actor_infos)

def get_elo(a_elo,b_elo, result):
    a_R = 1/(1+math.pow(10, (b_elo-a_elo)/400))
    if result==1:#a win
        new_a_elo=a_elo+100*(1-a_R)
    elif result==0:
        new_a_elo=a_elo+100*(0.5-a_R)
    else:
        new_a_elo=a_elo+100*(-a_R)
        if new_a_elo<0:
            new_a_elo=0
    return new_a_elo


@app.route('/update_actor_stats', methods=['POST'])
def update_actor_stats():
    win_actor=request.form['win']
    lose_actor=request.form['lose']
    win_count=-1
    win_elo=0
    for x in actor_table.find({"name":win_actor},{"win_count":1,"elo":1,"_id":0}):
        win_count=x["win_count"]
        win_elo=x["elo"]
    lose_count=-1
    lose_elo=0
    for x in actor_table.find({"name":lose_actor},{"lose_count":1,"_id":0}):
        lose_count=x["lose_count"]
        lose_elo=x["elo"]
    if win_count>=0 and lose_count>=0:
        new_win_elo=get_elo(win_elo,lose_elo, 1)
        new_lose_elo=get_elo(lose_elo,win_elo, -1)
        actor_table.update_one({"name":win_actor},{"$set":{"win_count":win_count+1,"elo":new_win_elo}})
        actor_table.update_one({"name":lose_actor},{"$set":{"lose_count":lose_count+1,"elo":new_lose_elo}})
    return "ok"


@app.route('/get_master_actors', methods=['POST'])
@auth.login_required
def get_master_actors():
    master_actor_infos=[]
    for x in actor_table.find({"master":auth.username()}):
        if not "elo" in x:
            continue
        info={}
        info["name"]=x["name"]
        info["color"]=x["color"]
        info["mass"]=x["mass"]
        info["ray_count"]=x["ray_count"]
        info["ray_range"]=x["ray_range"]
        info["speed"]=x["speed"]
        info["force"]=x["force"]
        info["elo"]=x["elo"]
        master_actor_infos.append(info)
    return json.dumps(master_actor_infos)

@app.route('/add_actor', methods=['POST'])
@auth.login_required
def add_actor():
    actor_data = request.form['actor_data']
    actor_obj = json.loads(actor_data)
    name=actor_obj['name']
    color=actor_obj['color']
    mass_p=actor_obj['mass']
    ray_count_p=actor_obj['ray_count']
    ray_range_p=actor_obj['ray_range']
    speed_p=actor_obj['speed']
    force_p=actor_obj['force']
    size_p=actor_obj['size']
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
    money=0
    for x in account_table.find({"name":auth.username()},{"_id":0,"money":1}):
        money=x["money"]
    if money>100:
        money=money-100
    else:
        return json.dumps(["money_not_enough"])
    mass=mass_p/2.0*(500-10)+10
    ray_count=int(ray_count_p/4.0*(18-9)+9)
    ray_range=int(ray_range_p/4.0*(30-10)+10)
    speed=speed_p/10.0*(2-0.5)+0.5
    force=force_p/2.0*(3-0.5)+0.5
    size=size_p/6.0*(2-0.5)+0.5
    actor_info={"name":name,"color":color,"mass":mass,"ray_count":ray_count, "ray_range":ray_range, "speed":speed, "force":force, "size":size, "train_steps":0, "win_count":0, "lose_count":0,"master":auth.username()}
    print(actor_info)
    actor_table.insert_one(actor_info)
    account_table.update_one({"name":auth.username()},{"$set":{"money":money}})
    return json.dumps(["ok"])

@app.route('/del_actor', methods=['POST'])
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

@app.route('/get_train_info', methods=['POST'])
@auth.login_required
def get_train_info():
    user = auth.username()
    return_info={}
    all_bid = list(account_table.find({"bid_train":{"$gt":0}},{"bid_train":1,"_id":0,"money":1}))
    max_bid=-1
    for bid in all_bid:
        if bid["money"]<bid["bid_train"]:
            continue
        if max_bid==1 or max_bid<bid["bid_train"]:
            max_bid=bid["bid_train"]
    if max_bid<0:
        max_bid==0
    for x in account_table.find({"name":user},{"_id":0,"bid_train":1,"bid_hour":1,"train_target":1,"train_enemy":1,"kick_reward":1,"point_reward":1,"pass_reward":1,"block_reward":1,"learning_rate":1}):
        if "bid_train" in x:
            return_info["train_status"]=x["train_status"]
            return_info["reward"]=x["reward"]
            return_info["win_rate"]=x["win_rate"]
            return_info["battle_time"]=x["battle_time"]
            return_info["bid_train"]=x["bid_train"]
            return_info["bid_hour"]=x["bid_hour"]
            return_info["train_target"]=x["train_target"]
            return_info["train_enemy"]=x["train_enemy"]
            return_info["kick_reward"]=x["kick_reward"]
            return_info["point_reward"]=x["point_reward"]
            return_info["pass_reward"]=x["pass_reward"]
            return_info["block_reward"]=x["block_reward"]
            return_info["learning_rate"]=x["learning_rate"]
            return_info["max_bid"]=max_bid
    return json.dumps(return_info)

@app.route('/pop_train_quene', methods=['POST'])
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

@app.route('/pop_battle_quene', methods=['POST'])
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

@app.route('/modify_train', methods=['POST'])
@auth.login_required
def modify_train():
    user = auth.username()
    data = request.form['data']
    obj = json.loads(data)
    bid_train=int(obj['bid_train'])
    train_target=obj['train_target']
    train_enemy=obj['train_enemy']
    kick_reward=float(obj['kick_reward'])
    point_reward=float(obj['point_reward'])
    pass_reward=float(obj['pass_reward'])
    block_reward=float(obj['block_reward'])
    bid_hour=int(obj['bid_hour'])
    find_actor=False
    for x in actor_table.find({"name":train_target},{"master":1,"_id":0}):
        if x["master"]!=user:
            return json.dumps(["train_target_not_yours"])
        else:
            find_actor=True
    if find_actor==False:
        return json.dumps(["train_target_not_exist"])
    find_actor=False
    for x in actor_table.find({"name":train_enemy},{"master":1,"_id":0}):
        find_actor=True
    if find_actor==False:
        return json.dumps(["train_enemy_not_exist"])
    re_string= get_model_name(train_enemy, False)
    if re_string=="":
        return json.dumps(["train_enemy_no_model"])
    account_table.update_one({"name":user},{"$set":{"bid_train":bid_train,"train_target":train_target,"train_enemy":train_enemy,"kick_reward":kick_reward,"point_reward":point_reward,"pass_reward":pass_reward,"block_reward":block_reward,"bid_hour":bid_hour}})
    return json.dumps(["ok"])

@app.route('/add_battle_quene', methods=['POST'])
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

@auth.get_password
def get_password(username):
    password=""
    for x in account_table.find({"name":username},{"_id":0,"password":1}):
        password=x["password"]
    if password=="":
        return None
    return password

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'invalid_access' } ), 401)

@app.route('/user_info', methods = ['POST'])
@auth.login_required
def user_info():
    account=auth.username()
    re=list(account_table.find({"name":account},{"_id":0,"password":0})) 
    if len(re)>0:
        return jsonify(re[0])
    return jsonify(["account_not_exist"])

@app.route('/login_create', methods=['POST'])
def regist():
    regist_data = request.form['regist_data']
    regist_obj = json.loads(regist_data)
    account=regist_obj["account"]
    password=regist_obj["password"]
    if len(account)>=1 and len(account)<20 and len(password)>=1 and len(password)<20:
        find_one=False
        for _ in account_table.find({"name":account},{"_id":0,"password":1}):
            find_one=True
        if find_one==False:
            while True:
                num_str=str(10000+random.randint(0, 9999))
                num_str=num_str[1:len(num_str)]
                re=list(account_table.find({"verify_code":num_str},{"_id":0,"name":1}))
                if len(re)==0:
                    break
            
            account_table.insert({"name":account, "password":password, "money":1000, "verify_code":num_str})
            return json.dumps(["regist_ok"])
        else:
            if password==password:
                return json.dumps(["login_ok"])
            else:
                return json.dumps(["password_wrong"])
    else:
        return json.dumps(["account_or_password_len_invalid"])

@app.route('/get_access_list', methods=['POST'])
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
