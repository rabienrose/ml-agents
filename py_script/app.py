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
    common_actor_infos=[]
    for item in actor_table.find({},{"_id":0}):
        if not "elo" in item:
            continue
        info={}
        info["name"]=item["name"]
        info["color"]=item["color"]
        info["elo"]=item["elo"]
        common_actor_infos.append(info)
    return json.dumps(common_actor_infos)

def myFunc(e):
  return e[0]

@app.route('/get_actor_list_str', methods=['GET', 'POST'])
def get_actor_list_str():
    info=""
    actor_elo_list=[]
    for item in actor_table.find({},{"_id":0}):
        if not "elo" in item:
            continue
        if item["elo"]<=0:
            continue
        actor_elo_list.append([item["elo"], item["name"], item["color"]])
    actor_elo_list.sort(key=myFunc,reverse=True)
    for item in actor_elo_list:
        info=info+item[1]+" "
        info=info+item[2]+" "
        info=info+str(int(item[0]))+" "
        info=info+","
    return info

def get_elo(a_elo,b_elo, result):
    a_R = 1/(1+math.pow(10, (b_elo-a_elo)/400))
    print(a_R)
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
    win_elo=1200
    for x in actor_table.find({"name":win_actor},{"win_count":1,"elo":1,"_id":0}):
        win_count=x["win_count"]
        if "elo" in x:
            win_elo=x["elo"]
    lose_count=-1
    lose_elo=1200
    for x in actor_table.find({"name":lose_actor},{"lose_count":1,"_id":0}):
        lose_count=x["lose_count"]
        if "elo" in x:
            lose_elo=x["elo"]
    if win_count>=0 and lose_count>=0:
        new_win_elo=int(get_elo(win_elo,lose_elo, 1))
        new_lose_elo=int(get_elo(lose_elo,win_elo, -1))
        actor_table.update_one({"name":win_actor},{"$set":{"win_count":win_count+1,"elo":new_win_elo}})
        actor_table.update_one({"name":lose_actor},{"$set":{"lose_count":lose_count+1,"elo":new_lose_elo}})
    return "ok"


@app.route('/get_master_actors', methods=['POST'])
@auth.login_required
def get_master_actors():
    master_actor_infos=[]
    for x in actor_table.find({"master":auth.username()}):
        info={}
        info["name"]=x["name"]
        info["color"]=x["color"]
        info["mass"]=x["mass"]
        info["ray_count"]=x["ray_count"]
        info["ray_range"]=x["ray_range"]
        info["speed"]=x["speed"]
        info["size"]=x["size"]
        info["force"]=x["force"]
        if "elo" in x:
            info["elo"]=x["elo"]
        else:
            info["elo"]=0
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
    actor_info={"name":name,"color":color,"mass":mass,"ray_count":ray_count, "ray_range":ray_range, "speed":speed, "force":force, "size":size, "train_steps":0, "win_count":0, "lose_count":0,"master":auth.username(),"elo":0}
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
    re_str=re_str+str(x["elo"])
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
    max_bid_info = get_max_bid_train()
    max_bid=0
    if len(max_bid_info)>0:
        max_bid=max_bid_info["max_bid"]
    for x in account_table.find({"name":user},{"_id":0,"battle_time":1,"win_rate":1,"reward":1,"bid_train":1,"bid_hour":1,"train_target":1,"train_enemy":1,"kick_reward":1,"point_reward":1,"pass_reward":1,"block_reward":1,"learning_rate":1,"training_num":1,"last_train_time":1}):
        if "bid_train" in x:
            if "training_num" in x:
                return_info["training_num"]=x["training_num"]
                if "last_train_time" in x:
                    print(time.time()-x["last_train_time"])
                    if time.time()-x["last_train_time"]>600:
                        return_info["training_num"]=0
                        account_table.update_one({"name":user},{"$set":{"training_num":0}})
            else:
                return_info["training_num"]=0
            if "reward" in x:
                return_info["reward"]=x["reward"]
                return_info["win_rate"]=x["win_rate"]
                return_info["battle_time"]=x["battle_time"]
            else:
                return_info["reward"]=0
                return_info["win_rate"]=0
                return_info["battle_time"]=0
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

@app.route('/done_train', methods=['POST'])
def done_train():
    train_actor=request.form['train_actor']
    reward=request.form['reward']
    win_rate=request.form['win_rate']
    battle_time=request.form['battle_time']
    master=""
    for x in actor_table.find({"name":train_actor},{"_id":0,"master":1}):
        master=x["master"]
    if master=="":
        return ""
    training_num=-1
    for x in account_table.find({"name":master},{"_id":0,"training_num":1}):
        training_num=x["training_num"]
    account_table.update_one({"name":master},{"$set":{"win_rate":win_rate,"reward":reward,"battle_time":battle_time,"training_num":training_num-1}})
    return ""

@app.route('/pop_train', methods=['POST'])
def pop_train():
    max_bid_info = get_max_bid_train()
    print(max_bid_info)
    if len(max_bid_info)>0:
        train_time=time.time()
        print(train_time)
        account_table.update_one({"name":max_bid_info["user"]},{"$set":{"money":max_bid_info["money"]-max_bid_info["max_bid"],"bid_hour":max_bid_info["bid_hour"]-1,"training_num":max_bid_info["training_num"]+1,"last_train_time":train_time}})
        train_info={"train_actor":max_bid_info["train_target"], "target_actor":max_bid_info["train_enemy"]}
        re_string = get_train_info_str(train_info)
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
    learning_rate=float(obj['learning_rate'])
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
    account_table.update_one({"name":user},{"$set":{"bid_train":bid_train,"train_target":train_target,"train_enemy":train_enemy,"kick_reward":kick_reward,"point_reward":point_reward,"pass_reward":pass_reward,"block_reward":block_reward,"bid_hour":bid_hour,"learning_rate":learning_rate}})
    return json.dumps(["ok"])

@app.route('/modify_battle', methods=['POST'])
@auth.login_required
def modify_battle():
    user = auth.username()
    data = request.form['data']
    obj = json.loads(data)
    bid_battle=int(obj['bid_battle'])
    battle_target=obj['battle_target']
    battle_enemy=obj['battle_enemy']
    if battle_enemy==battle_target:
        json.dumps(["can_not_battle_with_self"])
    find_one=False
    for x in actor_table.find({"name":battle_target},{"master":1,"_id":0}):
        find_one=True
        if x["master"]!=user:
            return json.dumps(["battle_target_not_yours"])
    if find_one==False:
        return json.dumps(["battle_target_not_exist"])
    if actor_table.find({"name":battle_enemy}).count(True)==0:
        return json.dumps(["battle_enemy_not_exist"])
    re_string= get_model_name(battle_target, False)
    if re_string=="":
        return json.dumps(["battle_target_no_model"])
    re_string= get_model_name(battle_enemy, False)
    if re_string=="":
        return json.dumps(["battle_enemy_no_model"])
    account_table.update_one({"name":user},{"$set":{"battle_target":battle_target,"battle_enemy":battle_enemy,"bid_battle":bid_battle}})
    return json.dumps(["ok"])

def get_max_bid_train():
    all_bid = list(account_table.find({"bid_train":{"$gt":0},"bid_hour":{"$gt":0}},{"bid_train":1,"_id":0,"money":1,"name":1}))
    max_bid=0
    max_bid_account=None
    for bid in all_bid:
        if bid["money"]<bid["bid_train"]:
            continue
        if max_bid==1 or max_bid<bid["bid_train"]:
            max_bid=bid["bid_train"]
            max_bid_account=bid["name"]
    max_bid_info={}
    if max_bid_account is not None:
        for x in account_table.find({"name":max_bid_account},{"_id":0,"train_target":1, "train_enemy":1,"money":1,"bid_hour":1,"training_num":1}):
            max_bid_info["max_bid"]=max_bid
            max_bid_info["train_target"]=x["train_target"]
            max_bid_info["train_enemy"]=x["train_enemy"]
            max_bid_info["bid_hour"]=x["bid_hour"]
            max_bid_info["user"]=max_bid_account
            max_bid_info["money"]=x["money"]
            if "training_num" in x:
                max_bid_info["training_num"]=x["training_num"]
            else:
                max_bid_info["training_num"]=0
            break
    return max_bid_info

def get_max_bid_battle():
    all_bid = list(account_table.find({"bid_battle":{"$gt":0}},{"bid_battle":1,"_id":0,"money":1,"name":1}))
    max_bid=0
    max_bid_account=None
    for bid in all_bid:
        if bid["money"]<bid["bid_battle"]:
            continue
        if max_bid==1 or max_bid<bid["bid_battle"]:
            max_bid=bid["bid_battle"]
            max_bid_account=bid["name"]
    max_bid_info={}
    if max_bid_account is not None:
        for x in account_table.find({"name":max_bid_account},{"_id":0,"battle_target":1, "battle_enemy":1,"money":1}):
            max_bid_info["max_bid"]=max_bid
            max_bid_info["battle_target"]=x["battle_target"]
            max_bid_info["battle_enemy"]=x["battle_enemy"]
            max_bid_info["user"]=max_bid_account
            max_bid_info["money"]=x["money"]
            break
    return max_bid_info

@app.route('/pop_battle', methods=['POST'])
def pop_battle():
    max_bid_info = get_max_bid_battle()
    if len(max_bid_info)>0:
        account_table.update_one({"name":max_bid_info["user"]},{"$set":{"money":max_bid_info["money"]-max_bid_info["max_bid"]}})
        rand_ind = randint(0, 1)
        if rand_ind==0:
            battle_info={"actor1":max_bid_info["battle_target"], "actor2":max_bid_info["battle_enemy"]}
        else:
            battle_info={"actor1":max_bid_info["battle_enemy"], "actor2":max_bid_info["battle_target"]}
        re_string = get_battle_info_str(battle_info)
    else:
        actor_list = list(actor_table.find({},{"_id":0,"name":1}))
        if len(actor_list)>1:
            while True:
                rand_ind1 = randint(0, len(actor_list)-1)
                rand_ind2 = randint(0, len(actor_list)-1)
                if rand_ind1==rand_ind2:
                    continue
                battle_info={"actor1":actor_list[rand_ind1]["name"], "actor2":actor_list[rand_ind2]["name"]}
                re_string = get_battle_info_str(battle_info)
                break
    return re_string

@app.route('/get_battle_info', methods=['POST'])
@auth.login_required
def get_battle_info():
    user = auth.username()
    return_info={}
    max_bid_info = get_max_bid_battle()
    max_bid=0
    if len(max_bid_info)>0:
        max_bid=max_bid_info["max_bid"]
    for x in account_table.find({"name":user},{"_id":0,"battle_target":1,"battle_enemy":1,"bid_battle":1}):
        return_info["max_bid"]=max_bid
        return_info["battle_target"]=x["battle_target"]
        return_info["battle_enemy"]=x["battle_enemy"]
        return_info["bid_battle"]=x["bid_battle"]
    return json.dumps(return_info)

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
    app.debug = True
    app.run('0.0.0.0', port=8001)
