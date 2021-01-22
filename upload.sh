
scp -r py_script root@123.57.250.31:~/mlagent
scp Project/soccer.x86_64 root@123.57.250.31:~/mlagent
scp -r Project/soccer_Data root@123.57.250.31:~/mlagent
scp config/ppo/SoccerTwos.yaml root@123.57.250.31:~/mlagent/config/ppo
scp -r ml-agents root@123.57.250.31:~/mlagent
scp -r ml-agents-envs root@123.57.250.31:~/mlagent
scp Project/UnityPlayer.so root@123.57.250.31:~/mlagent
# scp -r py_script/upload_model.py root@123.57.250.31:~/mlagent/py_script
scp -r py_script root@123.57.250.31:~/mlagent
scp -r ml-agents/mlagents/trainers/trainer/trainer_factory.py root@123.57.250.31:~/mlagent/ml-agents/mlagents/trainers/trainer/trainer_factory.py
#pip3 install torch -f https://download.pytorch.org/whl/torch_stable.html
#pip3 install -e ./ml-agents-envs
#pip3 install -e ./ml-agents