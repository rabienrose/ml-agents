import json
from pprint import pprint
import os
import os.path
from os import listdir
import shutil
from os.path import isfile, join
import pyproj
import math
import oss2
import numpy as np

import logging
import unittest
from logging import handlers

class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    } # prior: debug < info < warning < error < critical
    def __init__(self, filename, level='info', when='D', backCount=3, fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        fmt = '%(message)s'
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler() # print on screen
        sh.setFormatter(format_str)
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh)
        self.logger.addHandler(th)

_projections = {}
def zone(coordinates):
    if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
        return 32
    if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
        if coordinates[0] < 9:
            return 31
        elif coordinates[0] < 21:
            return 33
        elif coordinates[0] < 33:
            return 35
        return 37
    return int((coordinates[0] + 180) / 6) + 1


def letter(coordinates):
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]

def diff_vec2(v1, v2):
    return math.sqrt((v1[0]-v2[0])*(v1[0]-v2[0])+(v1[1]-v2[1])*(v1[1]-v2[1]))

def project(coordinates):
    z = zone(coordinates)
    l = letter(coordinates)
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    x, y = _projections[z](coordinates[0], coordinates[1])
    if y < 0:
        y += 10000000
    return z, l, x, y


def unproject(z, l, x, y):
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    if l < 'N':
        y -= 10000000
    lng, lat = _projections[z](x, y, inverse=True)
    return (lng, lat)
        
def get_name_from_gps(gps):
    return "["+str(round(gps[0]*100000)/100000.0)+"]["+str(round(gps[1]*100000)/100000.0)+"]"

def calc_garage_center(garage_root, garage_name):
    garage_addr=garage_root+"/"+garage_name
    posi_file_addr=garage_addr+"/posi.txt"
    gps_list=[]
    for file in os.listdir(garage_addr):
        if '.json' in file:
            with open(garage_addr+"/"+file, 'r') as f:
                data = json.load(f)
                lat=float(data['Entrance_location']['GPS_Latitude'])
                lon=float(data['Entrance_location']['GPS_Longitude'])
                gps_list.append([lat, lon])
    avg_gps=[0,0]
    count=len(gps_list)
    for item in gps_list:
        avg_gps[0]=avg_gps[0]+item[0]/count
        avg_gps[1]=avg_gps[1]+item[1]/count
    if os.path.isfile(posi_file_addr):
        os.remove(posi_file_addr)
    with open(posi_file_addr, 'w') as f:
        f.write(str(avg_gps[0])+","+str(avg_gps[1]));

def get_garage_center(garage_root, garage_name):
    garage_addr=garage_root+"/"+garage_name
    posi_file_addr=garage_addr+"/posi.txt"
    with open(posi_file_addr, 'r') as f:
        gps_str = f.read();
        gps_posi_vec = gps_str.split(',')
        coordinates=(float(gps_posi_vec[1]), float(gps_posi_vec[0]))
        posi = project(coordinates)
        return [posi,coordinates]
        
def transform_pt(angle, offset, pt):
    pt_ori=[pt[0]-offset[0], pt[1]-offset[1]]
    angle=-angle
    pt_rot_ori_x=math.cos(angle)*pt_ori[0]-math.sin(angle)*pt_ori[1]
    pt_rot_ori_y=math.sin(angle)*pt_ori[0]+math.cos(angle)*pt_ori[1]
    return [pt_rot_ori_x, pt_rot_ori_y]

def get_slot_pts(center, heading):
    para_depth  =2.2/2
    vert_depth  =4.8/2
    corner = [[vert_depth,para_depth],[vert_depth,-para_depth],[-vert_depth,-para_depth],[-vert_depth,para_depth]]
    re_corners=[]
    heading=heading/180*3.14151926
    for item in corner:
        temp_x=math.cos(heading)*item[0]-math.sin(heading)*item[1]
        temp_y=math.sin(heading)*item[0]+math.cos(heading)*item[1]
        re_corners.append([temp_x+center[0], temp_y+center[1]])
    return re_corners
    
def get_city_code_name():
    city_data={}
    with open("./data/china_coordinates.csv", 'r') as f:
        content = f.readlines()
        for city_str in content:
            city_str_vec = city_str.split(',')
            if len(city_str_vec)==4:
                id=int(city_str_vec[0])
                if id%100==0 and id%10000!=0 or id==110000 or id==120000 or id==500000 or id==310000:
                    if id!=419000 and id!=429000 and id!=469000 and id!=139000:
                        coordinates=(float(city_str_vec[2]), float(city_str_vec[3]))
                        posi = project(coordinates)
                        item={"posi":posi, "name":city_str_vec[1]}
                        city_data[id]=item
    city_data[-1]={"name":"other"}
    return city_data
    

def get_rank_info(file_name, trim_op=-1):
    re=[]
    f = open(file_name,'r')
    for line in f:
        str_splited = line.split(",")
        re.append([str_splited[0],int(str_splited[1])])
        if trim_op==1:
            if len(re)>=20:
                break
    if trim_op==2:
        trim_re=[]
        step=math.floor(len(re)/20)
        print(len(re))
        for i in range(0,len(re),step):
            trim_re.append(re[len(re)-i-1])
        re=trim_re
    f.close()
    return re

def write_json_to_oss(data, oss_addr,pre, bucket):
    temp_file=pre+"temp_file.json"
    f = open(temp_file, "w")
    json.dump(data, f)
    f.close()
    bucket.put_object_from_file(oss_addr, temp_file)

def put_folder_to_oss(folder, oss_path, bucket):
    for item in os.listdir(folder):
        temp_img_oss_addr=oss_path+"/"+item
        temp_img_local_addr=folder+"/"+item
        bucket.put_object_from_file(temp_img_oss_addr, temp_img_local_addr)

def set_task_status(oss_file, task, status, task_table):
    myquery = { "name": oss_file }
    newvalues = { "$set": { "task": task, "status": status} }
    task_table.update_one(myquery, newvalues, True)
    return
    
def del_task(name, task_table):
    task_table.delete_one({"name":name})
    return
    
def read_json_from_oss(oss_addr, pre, bucket):
    temp_file=pre+"temp_file.json"
    exist = bucket.object_exists(oss_addr)
    print(oss_addr)
    re_data=[]
    if exist:
        bucket.get_object_to_file(oss_addr, temp_file)
        f = open(temp_file, "r")
        try:
            re_data = json.load(f)
        except TypeError:
            print("Unable to deserialize the object")
        f.close()
    return re_data

def get_folder_from_oss(folder, oss_path, bucket):
    for b in oss2.ObjectIterator(bucket, prefix=oss_path):
        bucket.get_object_to_file(b.key, folder+"/"+b.key.split("/")[-1])
    return

def get_filelist_under_oss_path_from_oss(oss_path, bucket):
    filelist = []
    for b in oss2.ObjectIterator(bucket, prefix=oss_path):
        filelist.append(b.key.split("/")[-1])
    return filelist

def checkStatus(task, status, traj_name, task_table):
    bRet = False
    for x in task_table.find({"task":task, "status":status, "name": traj_name},{"_id":0,"name":1}):
        bRet = True
        break
    return bRet

def get_task_list(task, status, task_table):
    task_list=[]
    for x in task_table.find({"task":task, "status":status},{"_id":0,"name":1}):
        task_list.append(x["name"])
    return task_list

def read_list_from_oss(oss_addr, pre, bucket):
    temp_file=pre+"temp_file.json"
    exist = bucket.object_exists(oss_addr)
    print(oss_addr)
    re_data=[]
    if exist:
        bucket.get_object_to_file(oss_addr, temp_file)
        f = open(temp_file, "r")
        line = f.readline()
        while line:
            tmp_str_vec= line.split(" ")
            re_data.append(tmp_str_vec)
            line = f.readline()
        f.close()
    return re_data

def get_vins_from_trajname(trajname):
    vins_str=trajname.split("/")[-1].split("_")[1]
    return vins_str
    
def get_dist(v1, v2):
    x = v1[0]-v2[0]
    y = v1[1]-v2[1]
    z = v1[2]-v2[2]
    return math.sqrt(x*x+y*y+z*z)
    
def get_sub(v1, v2):
    x = v1[0]-v2[0]
    y = v1[1]-v2[1]
    z = v1[2]-v2[2]
    return [x,y,z]

def get_add(v1, v2):
    x = v1[0]+v2[0]
    y = v1[1]+v2[1]
    z = v1[2]+v2[2]
    return [x,y,z]
    
def get_dist2d(v1, v2):
    x = v1[0]-v2[0]
    y = v1[1]-v2[1]
    return math.sqrt(x*x+y*y)

def transform_2_gps_np(T_np, scu):
    temp_scu = scu.copy()
    temp_scu.append(1)
    temp_scu[2]=0
    scu_np = np.array(temp_scu).reshape(4,1)
    gps_posi_np=np.matmul(T_np, scu_np)
    return gps_posi_np.reshape(1,4).tolist()[0][0:3]

def transform_2_gps(T, scu):
    T_np = np.array(T).reshape(4,4)
    return transform_2_gps_np(T_np, scu)
    
def transform_2_gps_keep_h(T, scu):
    T_np = np.array(T).reshape(4,4)
    temp_scu = scu.copy()
    temp_scu.append(1)
    scu_np = np.array(temp_scu).reshape(4,1)
    gps_posi_np=np.matmul(T_np, scu_np)
    return gps_posi_np.reshape(1,4).tolist()[0][0:3]
    
def get_pose(t, theta):
    pose = np.identity(4)
    pose[0, 3]=t[0]
    pose[1, 3]=t[1]
    pose[2, 3]=t[2]
    pose[0, 0]=math.cos(theta)
    pose[0, 1]=-math.sin(theta)
    pose[1, 0]=math.sin(theta)
    pose[1, 1]=math.cos(theta)
    return pose
    
def get_angle_from_mat(T):
    angle = math.atan2( T[1,0], T[0,0] )
    return angle
    
def inter_seg(pt1, pt2, step):
    length=get_dist(pt2, pt1)
    out_pts=[pt1]
    if length<=0.1:
        return out_pts
    step_count=math.floor(length/step)
    dir=get_sub(pt2, pt1)
    unity_dir=[dir[0]/length, dir[1]/length, dir[2]/length]

    for i in range(0,step_count):
        new_pt_x=pt1[0]+unity_dir[0]*i*step
        new_pt_y=pt1[1]+unity_dir[1]*i*step
        new_pt_z=pt1[2]+unity_dir[2]*i*step
        out_pts.append([new_pt_x, new_pt_y, new_pt_z])
    return out_pts

def list_to_nparray(python_list):
    temp_count=0
    pc = np.zeros((len(python_list),3), dtype=np.float32)
    for posi in python_list:
        pc[temp_count,:]=np.array(posi).reshape(1,3)
        # pc[temp_count,2]=0
        temp_count=temp_count+1
    return pc

def del_file(filepath):
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    os.removedirs(filepath)
