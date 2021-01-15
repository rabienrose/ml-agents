import time
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

roomid=585480
cookie = "buvid3=0DEC0D0A-02A9-47B0-BBCB-EE903A23036F190959infoc; LIVE_BUVID=AUTO7115751187077836; stardustvideo=1; rpdid=|(k|km|~Ylkk0J'ul~luu)~J~; LIVE_PLAYER_TYPE=1; blackside_state=1; CURRENT_FNVAL=80; _uuid=FC612A5D-850F-AA1D-3F4A-E3547453892B17191infoc; bp_video_offset_3257122=469734366939084455; CURRENT_QUALITY=80; buivd_fp=0DEC0D0A-02A9-47B0-BBCB-EE903A23036F190959infoc; buvid_fp_plain=0DEC0D0A-02A9-47B0-BBCB-EE903A23036F190959infoc; bp_video_offset_1678662019=470458764711815006; bp_t_offset_1678662019=470522476256100477; bp_t_offset_3257122=470516102523535765; sid=6basqi43; bsource=search_baidu; finger=481832271; GIFT_BLOCK_COOKIE=GIFT_BLOCK_COOKIE; fingerprint3=f81747dd6d30ab5b150c4421a164bcd0; fingerprint=bfa826c35b93b95324cd97cf34f731c2; fingerprint_s=7473b67f5b98e8dd83624b8d5d37bd13; _dfcaptcha=b18ee69d16278d3d0439edf9453b4250; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1606662395,1608042769,1608433166,1608549141; Hm_lpvt_8a6e55dbd2870f0f5bc9194cddf32a02=1608549141; DedeUserID=3257122; DedeUserID__ckMd5=0459704718e252a3; SESSDATA=5f25ba14%2C1624101597%2C32391*c1; bili_jct=1521974d0f718c83521be6b669e70a6b; PVID=6"
cookie = "_uuid=FCC99AF5-6929-AB63-0328-E28ADFC55F9307057infoc; buvid3=0DEC0D0A-02A9-47B0-BBCB-EE903A23036F190959infoc; LIVE_BUVID=AUTO7115751187077836; sid=5d1ryd59; CURRENT_FNVAL=16; stardustvideo=1; rpdid=|(k|km|~Ylkk0J'ul~luu)~J~; CURRENT_QUALITY=64; LIVE_ROOM_ADMIN_UP_TIP=1; bp_video_offset_3257122=413359025648654201; bp_t_offset_3257122=413359025648654201; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1594727616,1594735626,1595092342,1595092364; GIFT_BLOCK_COOKIE=GIFT_BLOCK_COOKIE; bsource=search_baidu; _dfcaptcha=1259f52722c83e74aaf23ef61728d286; DedeUserID=3257122; DedeUserID__ckMd5=0459704718e252a3; SESSDATA=87c6ffe3%2C1610681708%2C0ed5a*71; bili_jct=2bb07096258d0d7e38d454c7460c8923; PVID=21"
token = re.search(r'bili_jct=(.*?);', cookie).group(1)

def send_msg(text):
    url = 'https://api.live.bilibili.com/ajax/msg'
    form = {
        'roomid': roomid,
        'visit_id': '',
        'csrf_token': token  # csrf_token就是cookie中的bili_jct字段;且有效期是7天!!!
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Cookie': cookie
    }
    html = requests.post(url, data=form)
    print(text)
    url_send = 'https://api.live.bilibili.com/msg/send'
    data = {
        'color': int("ff0000", 16),
        'fontsize': '25',
        'mode': '1',
        'msg': text,
        'rnd': 1595133024,
        'roomid': roomid,
        'csrf_token': token,
        'csrf': token
    }
    try:
        html_send = requests.post(url_send, data=data, headers=headers)
        result = html_send.json()
        if result['code'] == 0 and result['msg'] == '':
            print("succ")
    except:
        print("failed")

def game_thread():
    count=0
    while True:
        count=count+1
        start_time = time.time()
        time.sleep(0.5)

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
        elif m['msg_type'] == 'danmaku':
            uname = m['name']
            content = m['content']
            uid = m['id']
#            if uid!=3257122:
#                send_msg(send_text)
        elif m['msg_type'] == 'other':
            content=m["content"]
            print(m)
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

drop_db("b_live")
_thread.start_new_thread( game_thread,() )
asyncio.run(main("https://live.bilibili.com/"+str(roomid)))

        
