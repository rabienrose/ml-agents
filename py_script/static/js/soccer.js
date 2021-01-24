var account=""
var password=""

function get_master_actor(){
    $.ajax({
        type: 'POST',
        url: '../../get_master_actors',
        dataType: 'json',
        username: account, 
        password: password,
        success: function(data) {
            var str='<table border="1">'
            str=str+'<tr><td>名字</td><td>颜色</td><td>质量</td><td>观察力</td><td>视野范围</td><td>移动速度</td><td>击球力度</td><td>体型</td><td>天梯分数</td></tr>'
            if (data.length>0){
                for(var i=0; i<data.length; i++){
                    var str_row="<tr>"
                    str_row=str_row+"<td>"+data[i]["name"]+"</td>"
                    str_row=str_row+'<td style="color:#'+data[i]["color"]+';">'+data[i]["color"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["mass"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["ray_count"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["ray_range"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["speed"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["force"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["size"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["elo"]+"</td>"
                    str_row=str_row+"</tr>"
                    str=str+str_row
                }
            }
            str=str+"</table>"
            document.getElementById("master_actor_list").innerHTML=str
        },
    });
    
}

function show_actor_list(){
    $.ajax({
        type: 'GET',
        url: '../../get_actor_list',
        dataType: 'json',
        success: function(data) {
            data.sort((a, b) => (a.elo < b.elo) ? 1 : -1)
            console.log(data)
            var str='<table border="1">'
            str=str+'<tr><td>排名</td><td>名字</td><td>颜色</td><td>天梯分数</td></tr>'
            if (data.length>0){
                for(var i=0; i<data.length; i++){
                    var str_row="<tr>"
                    str_row=str_row+"<td>"+i+"</td>"
                    str_row=str_row+"<td>"+data[i]["name"]+"</td>"
                    str_row=str_row+'<td style="color:#'+data[i]["color"]+';">'+data[i]["color"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["elo"]+"</td>"
                    str_row=str_row+"</tr>"
                    str=str+str_row
                }
            }
            str=str+"</table>"
            document.getElementById("actor_list").innerHTML=str
        },
    });
}

function show_battle_status(){
    $.ajax({
        type: 'POST',
        url: '../../get_battle_info',
        username: account, 
        password: password,
        dataType: 'json',
        success: function(data) {
            if (!("max_bid" in data)){
                return
            }
            str=""
            str=str+"【竞拍出资："+data["bid_battle"]+"】"
            str=str+"【当前竞价："+data["max_bid"]+"】</br>"
            str=str+"【出战角色："+data["battle_target"]+"】"
            str=str+"【对战敌人："+data["battle_enemy"]+"】"
            document.getElementById("battle_status").innerHTML=str
        },
    });
}
function show_train_info(){
    $.ajax({
        type: 'POST',
        url: '../../get_train_info',
        username: account, 
        password: password,
        dataType: 'json',
        success: function(data) {
            if (!("max_bid" in data)){
                return
            }
            console.log(data)
            str=""
            str=str+"【正在训练："+data["training_num"]+"】"
            str=str+"【竞拍出资："+data["bid_train"]+"】"
            str=str+"【当前竞价："+data["max_bid"]+"】"
            str=str+"【竞拍时长："+data["bid_hour"]+"】</br>"
            str=str+"【奖励值："+data["reward"]+"】"
            str=str+"【胜率："+data["win_rate"]+"】"
            str=str+"【比赛时长："+data["battle_time"]+"】</br>"
            str=str+"【训练角色："+data["train_target"]+"】"
            str=str+"【训练对手："+data["train_enemy"]+"】</br>"
            str=str+"【触球奖励："+data["kick_reward"]+"】"
            str=str+"【进球奖励："+data["point_reward"]+"】"
            str=str+"【传球奖励："+data["pass_reward"]+"】"
            str=str+"【断球奖励："+data["block_reward"]+"】"
            str=str+"【学习率："+data["learning_rate"]+"】"
            
            document.getElementById("train_status").innerHTML=str
        },
    });
}

function modify_battle(){
    var bid_battle = document.getElementById("bid_battle").value
    var battle_target = document.getElementById("battle_target").value
    var battle_enemy = document.getElementById("battle_enemy").value
    if(isNaN(bid_battle)){
        alert("竞拍出资需要是数字")
        return
    }
    if (bid_battle>100000 || bid_battle<0){
        alert("竞拍出资时常超出允许范围")
        return
    }
    battle_data={}
    battle_data["bid_battle"]=bid_battle
    battle_data["battle_target"]=battle_target
    battle_data["battle_enemy"]=battle_enemy
    $.ajax({
        type: 'POST',
        url: '../../modify_battle',
        username: account, 
        password: password,
        data: { data: JSON.stringify(battle_data)},
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("添加成功")
                show_battle_status()
            }
            if (data[0]=="battle_target_not_yours"){
                alert("出战角色需要是你自己的角色")
            }
            if (data[0]=="battle_target_not_exist"){
                alert("出战角色不存在")
            }
            if (data[0]=="battle_enemy_not_exist"){
                alert("对战敌人角色不存在")
            }
            if (data[0]=="battle_target_no_model"){
                alert("出战角色没有AI")
            }
            if (data[0]=="battle_enemy_no_model"){
                alert("对战敌人没有AI")
            }
        },
        async: false
    });
}

function modify_train(){
    var bid_train = parseInt(document.getElementById("bid_train").value)
    var train_target = document.getElementById("train_target").value
    var train_enemy = document.getElementById("train_enemy").value
    var kick_reward = parseFloat(document.getElementById("kick_reward").value)
    var point_reward = parseFloat(document.getElementById("point_reward").value)
    var pass_reward = parseFloat(document.getElementById("pass_reward").value)
    var block_reward = parseFloat(document.getElementById("block_reward").value)
    var learning_rate = parseFloat(document.getElementById("learning_rate").value)
    var bid_hour = parseInt(document.getElementById("bid_hour").value)
    if(isNaN(bid_train)){
        alert("竞拍出资需要是数字")
        return
    }
    if (bid_train>100000 || bid_train<0){
        alert("竞拍出资时常超出允许范围")
        return
    }
    if(isNaN(kick_reward)){
        alert("触球奖励需要是数字")
        return
    }
    if (kick_reward>1 || kick_reward<0){
        alert("触球奖励超出允许范围")
        return
    }
    if(isNaN(point_reward)){
        alert("进球奖励需要是数字")
        return
    }
    if (point_reward>1 || point_reward<0){
        alert("进球奖励超出允许范围")
        return
    }
    if(isNaN(pass_reward)){
        alert("传球奖励需要是数字")
        return
    }
    if (pass_reward>1 || pass_reward<0){
        alert("传球奖励超出允许范围")
        return
    }
    if(isNaN(block_reward)){
        alert("断球奖励需要是数字")
        return
    }
    if (block_reward>1 || block_reward<0){
        alert("断球奖励超出允许范围")
        return
    }
    if(isNaN(learning_rate)){
        alert("学习率需要是数字")
        return
    }
    if (learning_rate>0.1 || learning_rate<0){
        alert("学习率超出允许范围")
        return
    }
    if(isNaN(bid_hour)){
        alert("竞拍时长需要是数字")
        return
    }
    if (bid_hour>1000 || bid_hour<0){
        alert("竞拍时长超出允许范围")
        return
    }
    train_data={}
    train_data["bid_train"]=bid_train
    train_data["train_target"]=train_target
    train_data["train_enemy"]=train_enemy
    train_data["kick_reward"]=kick_reward
    train_data["point_reward"]=point_reward
    train_data["pass_reward"]=pass_reward
    train_data["block_reward"]=block_reward
    train_data["bid_hour"]=bid_hour
    train_data["learning_rate"]=learning_rate
    $.ajax({
        type: 'POST',
        url: '../../modify_train',
        username: account, 
        password: password,
        data: { data: JSON.stringify(train_data)},
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("修改成功")
                show_train_info()
            }
            if (data[0]=="train_target_not_yours"){
                alert("只能训练自己的角色")
            }
            if (data[0]=="train_enemy_not_exist"){
                alert("训练对象不存在")
            }
            if (data[0]=="train_target_not_exist"){
                alert("训练角色不存在")
            }
            if (data[0]=="train_enemy_no_model"){
                alert("训练对象还没有AI")
            }
            if (data[0]=="can_not_battle_with_self"){
                alert("不能自己和自己对战")
            }
            
        },
        async: false
    });
}

function set_curr_train(){
    $.ajax({
        type: 'POST',
        url: '../../get_train_info',
        username: account, 
        password: password,
        dataType: 'json',
        success: function(data) {
            if (!("bid_train" in data)){
                return
            }
            document.getElementById("bid_train").value=data["bid_train"]
            document.getElementById("train_target").value=data["train_target"]
            document.getElementById("train_enemy").value=data["train_enemy"]
            document.getElementById("kick_reward").value=data["kick_reward"]
            document.getElementById("point_reward").value=data["point_reward"]
            document.getElementById("block_reward").value=data["block_reward"]
            document.getElementById("learning_rate").value=data["learning_rate"]
        },
    });
}

function set_curr_battle(){
    $.ajax({
        type: 'POST',
        url: '../../get_battle_info',
        username: account, 
        password: password,
        dataType: 'json',
        success: function(data) {
            if (!("bid_battle" in data)){
                return
            }
            document.getElementById("bid_battle").value=data["bid_battle"]
            document.getElementById("battle_target").value=data["battle_target"]
            document.getElementById("battle_enemy").value=data["battle_enemy"]
        },
    });
}

function get_input_points(){
    var name = document.getElementById("name").value
    var color = document.getElementById("color").value
    var mass = parseInt(document.getElementById("mass").value)
    var ray_count = parseInt(document.getElementById("ray_count").value)
    var ray_range = parseInt(document.getElementById("ray_range").value)
    var size = parseInt(document.getElementById("size").value)
    var speed = parseInt(document.getElementById("speed").value)
    var force = parseInt(document.getElementById("force").value)
    var actor_data={}
    if (name.includes(".") || name.includes("_") || name.includes(" ")){
        alert("名字不能包含. _ 和空格")
        return null
    }
    color_int = parseInt(color, 16);
    actor_data["name"]=name
    
    if (isNaN(color_int)){
        alert("颜色格式不对")
        return null
    }
    if (color_int>16777215 || color_int<0){
        alert("颜色格式不对")
        return null
    }
    actor_data["color"]=color
    if (isNaN(mass)){
        alert("质量需要是数字")
        return null
    }
    if (mass>2 || mass<0){
        alert("质量超出允许范围")
        return null
    }
    actor_data["mass"]=mass
    if (isNaN(ray_count)){
        alert("观察力需要是数字")
        return null
    }
    if (ray_count>4 || ray_count<0){
        alert("观察力超出允许范围")
        return null
    }
    actor_data["ray_count"]=ray_count
    if (isNaN(ray_range)){
        alert("视野需要是数字")
        return null
    }
    if (ray_range>4 || ray_range<0){
        alert("视野超出允许范围")
        return null
    }
    actor_data["ray_range"]=ray_range
    if (isNaN(size)){
        alert("体积需要是数字")
        return null
    }
    if (size>6 || size<0){
        alert("体积超出允许范围")
        return null
    }
    actor_data["size"]=size
    if (isNaN(speed)){
        alert("移动速度需要是数字")
        return null
    }
    if (speed>10 || speed<0){
        alert("移动速度超出允许范围")
        return null
    }
    actor_data["speed"]=speed
    if (isNaN(force)){
        alert("击球力量需要是数字")
        return null
    }
    if (force>2 || force<0){
        alert("击球力量超出允许范围")
        return null
    }
    actor_data["force"]=force
    return actor_data;
}

function update_points(){
    actor_data = get_input_points()
    sum_points=0
    for (key in actor_data){
        if (key!="name" && key!="color"){
            sum_points=sum_points+actor_data[key]
        }
    }
    str_temp=""
    if (sum_points==14){
        str_temp='<div style="color:#00ff00">'+sum_points+'/14(当前点数/总点数)<div>'
    }else{
        str_temp='<div style="color:#ff0000">'+sum_points+'/14(当前点数/总点数)<div>'
    }
    document.getElementById("remain_points").innerHTML=str_temp
}

function add_actor(){
    actor_data = get_input_points()
    if (actor_data==null){
        return
    }
    
    $.ajax({
        type: 'POST',
        url: '../../add_actor',
        data: { actor_data: JSON.stringify(actor_data)},
        username: account, 
        password: password,
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("新建角色成功")
                show_actor_list()
                get_account_info()
            }
            if (data[0]=="existed_name"){
                alert("角色名已存在")
            }
            if (data[0]=="existed_color"){
                alert("角色颜色已存在")
            }
            if (data[0]=="money_not_enough"){
                alert("币不够")
            }            
        },
        async: false
    });
}

function update_local_password(){
    if ("account" in localStorage && localStorage["account"]!=""){
        account=localStorage["account"]
        password=localStorage["password"]
    }
}

function clear_local_password(){
    if ("account" in localStorage){
        localStorage["account"]=""
        localStorage["password"]=""
        account=""
        password=""
    }
}

function set_local_password(account_, password_){
    localStorage.setItem("account", account_);
    localStorage.setItem("password", password_);
}

function get_account_info(){
    console.log("account "+account)
    if (account==""){
        return;
    }
    $.ajax({
        url: "../../user_info",
        type: 'POST',
        dataType: 'json',
        username: account, 
        password: password,
        success: function(data){
            console.log(data)
            if ("name" in data){
                b_account_id="未绑定"
                if ("b_account_id" in data){
                    b_account_id=data["b_account_id"]
                    document.getElementById("bind_info").style.display = "none"
                }else{
                    document.getElementById("bind_info").style.display = "block"
                    document.getElementById("bind_info").innerHTML="请用站账号在智能体直播间发送弹幕"+data["verify_code"]+"。系统检测到后，会绑定B站账号。刷新页面可以看到绑定结果。"
                }
                document.getElementById("account_info").innerHTML="<b>账号：</b>"+data["name"]+"</br><b>币：</b>"+data["money"]+"</br><b>B站账号：</b>"+b_account_id
            }
        },
        error: function (request, status, error) {
            clear_local_password()
        }
    });
}


function login_regist(){
    var account = document.getElementById("account").value
    var password = document.getElementById("password").value
    $.ajax({
        url: "../../login_create",
        type: 'POST',
        dataType: 'json',
        data: { regist_data: JSON.stringify({"account":account, "password":password})},
        success: function(data){
            console.log(data[0])
            if (data[0]=="regist_ok"){
                set_local_password(account, password)
                update_local_password()
                alert("注册成功")
                document.getElementById("loginui").style.display = "none"
                document.getElementById("user_area").style.display = "block"
                get_account_info()
            }else if(data[0]=="login_ok"){
                alert("登录成功")
                set_local_password(account, password)
                update_local_password()
                document.getElementById("loginui").style.display = "none"
                document.getElementById("user_area").style.display = "block"
                get_account_info()
            }else if(data[0]=="password_wrong"){
                alert("密码错误")
            }else if(data[0]=="account_or_password_len_invalid"){
                alert("账号密码长度不符合要求")
            }
        },
    });
}

$(document).ready(function(){
    $.ajaxSetup({
        async: false
    });
    //show_elo_list()
    update_local_password()
    get_account_info()
    var x = document.getElementById("loginui");
    if (password=="") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
    if (password!="") {
        document.getElementById("user_area").style.display = "block"
        update_points()
        get_master_actor()
        show_train_info()
        show_battle_status()
    }
    show_actor_list()


})
