function show_actor_list(){
    $.ajax({
        type: 'GET',
        url: '../../get_actor_list',
        dataType: 'json',
        success: function(data) {
            var str='<table border="1">'
            str=str+'<tr><td>名字</td><td>颜色</td><td>质量</td><td>观察力</td><td>视野范围</td><td>移动速度</td><td>击球力度</td><td>胜利</td><td>失败</td></tr>'
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
                    str_row=str_row+"<td>"+data[i]["win_count"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["lose_count"]+"</td>"
                    str_row=str_row+"</tr>"
                    str=str+str_row
                }
            }
            str=str+"</table>"
            document.getElementById("actor_list").innerHTML=str
        },
    });
}

function show_battle_list(){
    $.ajax({
        type: 'GET',
        url: '../../show_battle_qunue',
        dataType: 'json',
        success: function(data) {
            var str='<table border="1">'
            str=str+'<tr><td>角色1</td><td>角色2</td></tr>'
            if (data.length>0){
                for(var i=0; i<data.length; i++){
                    var str_row="<tr>"
                    str_row=str_row+"<td>"+data[i]["actor1"]+"</td>"
                    str_row=str_row+"<td>"+data[i]["actor2"]+"</td>"
                    str_row=str_row+"</tr>"
                    str=str+str_row
                }
            }
            str=str+"</table>"
            document.getElementById("battle_list").innerHTML=str
        },
    });
}
function show_train_list(){
    $.ajax({
        type: 'GET',
        url: '../../show_train_qunue',
        dataType: 'json',
        success: function(data) {
            var str='<table border="1">'
            str=str+'<tr><td>训练角色</td><td>对手</td><td>次数</td></tr>'
            if (data.length>0){
                train_count={}
                for(var i=0; i<data.length; i++){
                    combine_name=data[i]["train_actor"]+"."+data[i]["target_actor"]
                    if (combine_name in train_count){
                        train_count[combine_name]=train_count[combine_name]+1
                    }else{
                        train_count[combine_name]=1
                    }
                }
                for(var key in train_count){
                    vec_names = key.split(".")
                    var str_row="<tr>"
                    str_row=str_row+"<td>"+vec_names[0]+"</td>"
                    str_row=str_row+"<td>"+vec_names[1]+"</td>"
                    str_row=str_row+"<td>"+train_count[key]+"</td>"
                    str_row=str_row+"</tr>"
                    str=str+str_row
                }
            }
            str=str+"</table>"
            document.getElementById("train_list").innerHTML=str
        },
    });
}

function add_battle(){
    var actor1 = document.getElementById("actor1").value
    var actor2 = document.getElementById("actor2").value
    battle_data={}
    battle_data["actor1"]=actor1
    battle_data["actor2"]=actor2
    $.ajax({
        type: 'POST',
        url: '../../add_battle_quene',
        data: { battle_data: JSON.stringify(battle_data)},
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("添加成功")
                show_battle_list()
            }
            if (data[0]=="actor1_not_exist"){
                alert("角色1不存在")
            }
            if (data[0]=="actor2_not_exist"){
                alert("角色2不存在")
            }
            if (data[0]=="actor1_no_model"){
                alert("角色1不存在AI")
            }
            if (data[0]=="actor2_no_model"){
                alert("角色2不存在AI")
            }
        },
        async: false
    });
}

function add_train(){
    var train_actor = document.getElementById("train_actor").value
    var target_actor = document.getElementById("target_actor").value
    var train_count = parseInt(document.getElementById("train_count").value)
    if(isNaN(train_count)){
        if (isNaN(train_count)){
            alert("训练次数需要是数字")
            return
        }
    }
    if (train_count>1000 || train_count<0){
        alert("训练次数超出允许范围")
        return
    }
    train_data={}
    train_data["train_actor"]=train_actor
    train_data["target_actor"]=target_actor
    train_data["train_count"]=train_count
    $.ajax({
        type: 'POST',
        url: '../../add_train_quene',
        data: { train_data: JSON.stringify(train_data)},
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("添加成功")
                show_train_list()
            }
            if (data[0]=="train_actor_not_exist"){
                alert("训练角色不存在")
            }
            if (data[0]=="target_actor_not_exist"){
                alert("目标角色不存在")
            }
        },
        async: false
    });
}

function add_actor(){
    var name = document.getElementById("name").value
    var color = document.getElementById("color").value
    var mass = parseInt(document.getElementById("mass").value)
    var ray_count = parseInt(document.getElementById("ray_count").value)
    var ray_range = parseInt(document.getElementById("ray_range").value)
    var size = parseInt(document.getElementById("size").value)
    var speed = parseFloat(document.getElementById("speed").value)
    var force = parseFloat(document.getElementById("force").value)
    var actor_data={}
    if (name.includes(".") || name.includes("_") || name.includes(" ")){
        alert("名字不能包含. _ 和空格")
        return
    }
    color_int = parseInt(color, 16);
    actor_data["name"]=name
    
    if (isNaN(color_int)){
        alert("颜色格式不对")
        return
    }
    if (color_int>16777215 || color_int<0){
        alert("颜色格式不对")
        return
    }
    actor_data["color"]=color
    if (isNaN(mass)){
        alert("质量需要是数字")
        return
    }
    if (mass>500 || mass<10){
        alert("质量超出允许范围")
        return
    }
    actor_data["mass"]=mass
    if (isNaN(ray_count)){
        alert("观察力需要是数字")
        return
    }
    if (ray_count>18 || ray_count<9){
        alert("观察力超出允许范围")
        return
    }
    actor_data["ray_count"]=ray_count
    if (isNaN(ray_range)){
        alert("视野需要是数字")
        return
    }
    if (ray_range>30 || ray_range<10){
        alert("视野超出允许范围")
        return
    }
    actor_data["ray_range"]=ray_range
    if (isNaN(size)){
        alert("体积需要是数字")
        return
    }
    if (size>2 || size<0.5){
        alert("体积超出允许范围")
        return
    }
    if (isNaN(speed)){
        alert("移动速度需要是数字")
        return
    }
    if (speed>2 || speed<0.5){
        alert("移动速度超出允许范围")
        return
    }
    actor_data["speed"]=speed
    if (isNaN(force)){
        alert("击球力量需要是数字")
        return
    }
    if (force>3 || force<0.5){
        alert("击球力量超出允许范围")
        return
    }
    actor_data["force"]=force
    actor_data["size"]=size
    console.log(actor_data)
    $.ajax({
        type: 'POST',
        url: '../../add_actor',
        data: { actor_data: JSON.stringify(actor_data)},
        dataType: 'json',
        success: function(data) {
            if (data[0]=="ok"){
                alert("新建角色成功")
                show_actor_list()
            }
            if (data[0]=="existed_name"){
                alert("角色名已存在")
            }
            if (data[0]=="existed_color"){
                alert("角色颜色已存在")
            }
            
        },
        async: false
    });

}


$(document).ready(function(){
    $.ajaxSetup({
        async: false
    });
    show_actor_list()
    show_battle_list()
    show_train_list()
})
