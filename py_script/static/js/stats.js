function show_list(){
    $.ajax({
        type: 'GET',
        url: '../../get_access_list',
        dataType: 'json',
        success: function(data) {
            console.log(data)
            var str='<table border="1">'
            str=str+'<tr><td></td><td>用户名字</td><td>上次访问时间</td><td>访问次数</td></tr>'
            if (data.length>0){
                for(var i=0; i<data.length; i++){
                    str=str+'<tr><td>'+i+'</td><td>'+data[i]["name"]+'</td><td>'+data[i]["time"]+'</td><td>'+data[i]["count"]+'</td></tr>'
                }
            }
            str=str+"</table>"
            document.getElementById("usr_list_div").innerHTML=str
        },
    })
}


$(document).ready(function(){
    $.ajaxSetup({
        async: false
    });
})
