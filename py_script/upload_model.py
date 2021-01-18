import time
import os
from common.config import get_config
import pathlib
from os.path import isfile, join
[bucket, myclient]=get_config()

upload_model_folder="/workspace/results/chamo"
oss_path="model"
while True:
    if not os.path.exists(upload_model_folder):
        time.sleep(60)
        continue
    for filename in os.listdir(upload_model_folder):
        file_addr=upload_model_folder+"/"+filename
        if isfile(file_addr):
            continue
        if filename=="run_logs":
            continue
        sub_folder=file_addr
        onnx_list=[]
        bp_name=""
        for filename1 in os.listdir(sub_folder):
            if ".onnx" in filename1:
                vec_name=filename1.split("-")
                bp_name=vec_name[0]
                step=int(vec_name[1].split(".")[0])
                onnx_list.append(step)
        onnx_list.sort(reverse=True)
        count=0
        for item in onnx_list:
            # oss_filename=bp_name+str(count)+".onnx"
            local_name=bp_name+"-"+str(item)+".onnx"
            if count>=4:
                break
            count=count+1
            oss_file_path = oss_path+"/"+local_name
            exist = bucket.object_exists(oss_file_path)
            if not exist:
                print(local_name)
                temp_img_local_addr=sub_folder+"/"+local_name
                bucket.put_object_from_file(oss_file_path, temp_img_local_addr)
    time.sleep(60)