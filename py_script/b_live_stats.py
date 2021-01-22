import time
import asyncio
import danmaku
import _thread
import requests, re
import copy
import pymongo
from common.config import get_config
from common.config import drop_db
[bucket, myclient]=get_config()
mydb=myclient["b_live"]
user_table = mydb["user"]
account_table = mydb["account"]
roomid=585480
async def printer(q):
    global new_add_list
    while True:
        m = await q.get()
        if m['msg_type'] == 'gift':
            #id=random.randint(0, 999999)
            data=m["raw"]
            coin_count = data["total_coin"]
            send_name=data["uname"]
            if len(send_name)>5:
                send_name=send_name[0:6]
            uid=data["uid"]
            giftType=data["giftType"]
            gift_name=data["giftName"]
            print(data)
            re=list(account_table.find({"b_account_id":uid},{"_id":0,"name":1,"money":1}))
            if len(re)>0:
                account_table.update_one({"name":re[0]["name"]},{"$set":{"money":re[0]["money"]+coin_count}})
            else:
                re=list(user_table.find({"user_id":uid},{"_id":0, "coin":1}))
                old_coin=0
                if "coin" in re[0]:
                    old_coin=re[0]["coin"]
                if len(re)>0:
                    user_table.update_one({"user_id":uid},{"$set":{"coin":old_coin+coin_count}})
            print(gift_name)
        elif m['msg_type'] == 'danmaku':
            uname = m['name']
            content = m['content']
            uid = m['id']
            if len(content)==4 and content.isdigit():
                re=list(account_table.find({"verify_code":content},{"_id":0,"name":1}))
                print(re[0])
                if len(re)>0:
                    re1=list(account_table.find({"b_account_id":uid},{"_id":0,"name":1}))
                    if len(re1)>0:
                        print("already bind to this b account!!!")
                        continue
                    agent_account = re[0]["name"]
                    re=list(user_table.find({"user_id":uid},{"_id":0, "coin":1}))
                    b_old_coin=0
                    if len(re)>0 and "coin" in re[0]:
                        b_old_coin=re[0]["coin"]
                        user_table.update_one({"user_id":uid},{"$set":{"coin":0}})
                    re=list(account_table.find({"name":agent_account},{"_id":0,"money":1}))
                    account_money=0
                    if len(re)>0 and "money" in re[0]:
                        account_money=re[0]["money"]
                    account_table.update_one({"name":agent_account},{"$set":{"b_account_id":uid,"b_account_name":uname,"money":b_old_coin+account_money, "verify_code":-1}})
                    
        elif m['msg_type'] == 'other':
            content=m["content"]
            if not type(content) is dict:
                continue
            if "cmd" in content and content['cmd']=="INTERACT_WORD":
                data=content["data"]
                print(data["uid"],data["uname"],data["timestamp"])
                handle_user(data["uid"], data["uname"], data["timestamp"])
            
                
            
def handle_user(user_id, user_name, timestamp):
    find_user=False
    for x in user_table.find({"user_id":user_id}):
        count_enter=x["count"]+1
        user_table.update_one({"user_id":user_id},{"$set":{"count":count_enter,"timestamp":timestamp}})
        find_user=True
    if find_user==False:
        user_table.insert_one({"user_id":user_id, "user_name":user_name, "count":1,"timestamp":timestamp})

async def main(url):
    q = asyncio.Queue()
    dmc = danmaku.DanmakuClient(url, q)
    asyncio.create_task(printer(q))
    await dmc.start()

asyncio.run(main("https://live.bilibili.com/"+str(roomid)))

        
