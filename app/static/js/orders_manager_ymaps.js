var points = []
var map_obj;

function click_on_order(order_id){
    var tr = document.querySelector("#"+order_id)
    for (var i = 0; i < points.length; i++){
        if (points[i].properties._data.order_id == order_id){
            var point = points[i]
            break
        }
    }
    if (point.properties._data.choosen){
        point.options.set("preset", "islands#blackStretchyIcon")
        tr.className =""
        point.properties._data.choosen = false
    } else {
        point.options.set("preset", "islands#blueStretchyIcon")
        tr.className ="table-primary"
        point.properties._data.choosen = true
    }
}


//Кнопка подгрузки заказов
$("#get_orders_btn").click(function () {
//    обновляем карту
    document.querySelector("#orders_list").innerHTML = ''
    if (!!map_obj){
        map_obj.destroy()
    }
    map_obj = new ymaps.Map("map", {
        center: [55.76, 37.64],
        zoom: 10
    });
//    запрашиваем заказы
    $.get({
        url: "/admin/get_orders",
            success: function (result) {
                var orders = JSON.parse(result)['orders']

//              для каждого заказа:
                for (const order of orders){
//                  создаем строчку
                    var tr = document.createElement("tr")
                    tr.id = order["order_id"]
                    $("<td>").html(order["cluster"]).appendTo(tr)
                    $("<td>").html(order["order_id"]).appendTo(tr)
                    $("<td>").html(order["del_time_interval"]).appendTo(tr)
                    $("<td>").html(order["weight"]).appendTo(tr)
                    $("<td>").html(order["positions"]).appendTo(tr)
                    $("<td>").html(order["comment"]).appendTo(tr)
                    document.querySelector("#orders_list").appendChild(tr)
                    tr.onclick = function(){click_on_order(order["order_id"])}

//                  создаем точку
                    new_point = new ymaps.GeoObject({
                        geometry: {
                            type: "Point",
                            coordinates: [order['lat'], order['long']]
                        },
                        properties: {
                            iconContent: order['cluster'] + ": " + order['order_id'],
                            order_id: order['order_id'],
                            choosen: false
                        }
                    },{
                        preset: 'islands#blackStretchyIcon',
                    })

//                  событие клика по точке
                    points.push(new_point)
                    new_point.events.add('click', function (e) {
                        var target = e.get('target');
                        order_id = target.properties.get("order_id")
                        click_on_order(order_id)
                    })

//                  добавляем точку на карту
                    map_obj.geoObjects.add(new_point)

                }
            }
  });
});