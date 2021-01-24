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
        for filename1 in os.listdir(sub_folder):
            if ".onnx" in filename1:
                oss_file_path = oss_path+"/"+filename1
                print(filename1)
                temp_img_local_addr=sub_folder+"/"+filename1
                bucket.put_object_from_file(oss_file_path, temp_img_local_addr)
                os.remove(temp_img_local_addr)
    time.sleep(60)