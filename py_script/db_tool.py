import oss2
import os
import os.path
from datetime import date
from shutil import copyfile
import shutil
import datetime
import time
import json
import sys
import struct
import math
import pymongo
from common.config import get_config
from common.config import drop_db
[bucket, myclient]=get_config()
mydb=myclient["b_live"]
# user_table = mydb["user"]
actor_table = mydb["actor"]
train_table = mydb["train"]
#actor_table.insert_one({"name":"chamo","colro":"66ccff","id":0,"mass":50,"ray_count":180, "ray_range":10, "speed":0.2, "force":1, "size":1, "train_steps":0, "win_count":0, "lose_count":0})
#train_table.insert_one({"train_actor":"chamo", "target_team":"self","train_count":10})
# train_table.delete_many({"train_actor":"茶末"})
# train_table.insert_one({"train_actor":"chamo", "target_actor":"chamo"})
# for x in train_table.find({}):
#     print(x)
# for x in actor_table.find({}):
#     print(x)

train_table.delete_many({"train_actor":"chamo"})
# task_table.update_many({"task":"locmap"},{"$set":{"task":"group","status":2}})
#task_table.update_many({"name":{"$regex" : ".*LMVAGL7U0KA001658.*"}},{"$set":{"task":"feature","status":2}})
#task_table.update_one({"name":"05-09-2020-17-40-24_LMVHFEFZ8KA752551_in"},{"$set":{"task":"test_crash","status":2}})
#for x in task_table.find({"name": {"$regex" : ".*L1NSPGHB2LA000111.*"}}):
#    print(x)
#drop_db("test_e2e")
#print(task_table.count_documents({"task":"feature","status":2}))
# enter_more_than_one=0
# min_time=-1
# max_time=-1
# total_count=0
# for x in user_table.find({}):
#     timestamp=x["timestamp"]
#     count=x["count"]
#     total_count=total_count+1
#     print(x["user_name"], count)
#     if count>1:
#         enter_more_than_one=enter_more_than_one+1
#     if min_time>timestamp or min_time==-1:
#         min_time=timestamp
#     if max_time<timestamp or max_time==-1:
#         max_time=timestamp
# print("duration",float(max_time-min_time)/60)
# print("enter_per_sec",total_count/float(max_time-min_time)*60)
# print("revisit",enter_more_than_one)

# new_time=time.time()
# for x in user_table.find({"user_name":"yzhang1576"},{"_id":0,"count":1}):
#     print(x)
# print(time.time()-new_time)
    
#task_table.delete_many({"name":"10-09-2020-15-29-59_LMVAGL7U0KA001658"})
#garage_table.delete_many({})

# drop_db("b_live")
#list_db()

#def del_folder(oss_folder):
#    for obj in oss2.ObjectIterator(bucket, prefix=oss_folder):
#        bucket.delete_object(obj.key)
#
#del_folder("ws_e2e")
