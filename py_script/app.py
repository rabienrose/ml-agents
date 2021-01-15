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

@app.route('/get_actor_list', methods=['GET', 'POST'])
def get_actor_list():
    actor_list = list(actor_table.find({},{"_id":0}))
    return json.dumps(actor_list)

@app.route('/get_actor_info', methods=['GET', 'POST'])
def get_actor_info():
    actor_list = list(actor_table.find({},{"_id":0}))
    return json.dumps(actor_list)

@app.route('/add_actor', methods=['GET', 'POST'])
def add_actor():
    name=request.args.get('name')
    color=request.args.get('color')
    mass=request.args.get('mass')
    ray_count=request.args.get('ray_count')
    ray_range=request.args.get('ray_range')
    speed=request.args.get('speed')
    force=request.args.get('force')
    size=request.args.get('size')
    existed=False
    for x in actor_table.find({"name":name}):
        existed=True
    if existed:
        return json.dumps(["existed"])
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
    re_str=re_str+str(x["mass"])
    return re_str

def get_model_name(actor_name):
    model_name=""
    onnx_list=[]
    bp_name=""
    for obj in oss2.ObjectIterator(bucket, prefix="model/"+actor_name):
        str_vec=obj.key.split("/")
        if len(str_vec)==2:
            model_name=str_vec[-1]
            vec_name=model_name.split("-")
            bp_name=vec_name[0]
            step=int(vec_name[1].split(".")[0])
            onnx_list.append(step)
    onnx_list.sort(reverse=True)
    count=0
    filtered_models=[]
    for item in onnx_list:
        # oss_filename=bp_name+str(count)+".onnx"
        local_name=bp_name+"-"+str(item)+".onnx"
        if count<4:
            filtered_models.append(local_name)
        else:
            oss_file_path = "model"+"/"+local_name
            bucket.delete_object(oss_file_path)
        count=count+1
    if len(filtered_models)>=1:
        rand_ind = randint(0, len(filtered_models)-1)
        print("choose: "+filtered_models[rand_ind])
        return filtered_models[rand_ind]
    else:
        return ""

@app.route('/pop_train_quene', methods=['GET', 'POST'])
def pop_train_quene():
    train_list = list(train_table.find({}))
    re_string=""
    if len(train_list)>0:
        first_train=train_list[0]
        find_actor_b=False
        for x in actor_table.find({"name":first_train["train_actor"]}):
            info_string = get_actor_info_string(x)
            re_string=re_string+info_string+","
            find_actor_b=True
        if find_actor_b==False:
            return "train_quene_empty"
        find_actor_b=False
        for x in actor_table.find({"name":first_train["target_actor"]}):
            info_string = get_actor_info_string(x)
            re_string=re_string+info_string+","
            find_actor_b=True
        if find_actor_b==False:
            return "train_quene_empty"
        re_string=re_string+get_model_name(first_train["target_actor"])
        train_table.delete_one({"_id":first_train["_id"]})
        return re_string
    return "train_quene_empty"

@app.route('/add_train_quene', methods=['GET', 'POST'])
def add_train_quene():
    train_actor=request.args.get('train_actor')
    target_actor=request.args.get('target_actor')
    train_count=int(request.args.get('train_count'))
    if actor_table.find({"name":train_actor}).count(True)==0:
        return json.dumps(["train_actpr not exist"])
    if target_actor!="self" and target_actor!="all":
        if actor_table.find({"name":target_actor}).count(True)==0:
            return json.dumps(["target_actor not exist"])
    if target_actor=="self":
        for _ in range(train_count):
            train_table.insert_one({"train_actor":train_actor, "target_actor":train_actor})
    return json.dumps(["ok"])

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
    app.debug = True
    app.run('0.0.0.0', port=8001)
