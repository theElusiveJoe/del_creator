var points;
var map_obj;
var route_obj;

var cluster_color_mapping = {
    // для нулевого кластера
    0: 'islands#grayStretchyIcon',
    // для выделенных
    'selected': 'islands#redStretchyIcon',
    // популярные
    1: 'islands#blueStretchyIcon',
    2: 'islands#darkGreenStretchyIcon',
    3: 'islands#nightStretchyIcon',
    4: 'islands#violetStretchyIcon',
    5: 'islands#pinkStretchyIcon',
    6: 'islands#brownStretchyIcon',
    // остальные
    7: 'islands#darkOrangeStretchyIcon',
    8: 'islands#blackStretchyIcon',
    9: 'islands#yellowStretchyIcon',
    10: 'islands#darkBlueStretchyIcon',
    11: 'islands#greenStretchyIcon',
    12: 'islands#orangeStretchyIcon',
    13: 'islands#lightBlueStretchyIcon',
    14: 'islands#oliveStretchyIcon'
}


function load_orders(cl_num) {
    console.log('LOADING CLUSTER', cl_num)
    //    обновляем карту
    document.querySelector("#orders_list").innerHTML = ''
    if (!!map_obj) {
        map_obj.destroy()
    }
    map_obj = new ymaps.Map("map", {
        center: [55.76, 37.64],
        zoom: 9
    });
    //    запрашиваем заказы
    $.get({
        url: "/admin/get_orders",
        data: {
            'cluster_num': cl_num
        },
        success: function (result) {
            var orders = JSON.parse(result)['orders']

            clusters = []
            points = []

            // для каждого заказа:
            for (const order of orders) {
                // создаем строчку
                var tr = document.createElement("tr")
                tr.id = 'order' + order["order_id"]
                tr.setAttribute("data-mdb-sortable", "sortable")
                tr.classList.add("sortable-item")
                $("<td>").html(order["order_id"]).appendTo(tr)
                $("<td>").html(order["del_time_interval"]).appendTo(tr)
                $("<td>").html(order["weight"]).appendTo(tr)
                $("<td>").html(order["positions"]).appendTo(tr)
                $("<td>").html(order["comment"]).appendTo(tr)
                document.querySelector("#orders_list").appendChild(tr)
                // tr.onclick = function () { click_on_order(order["order_id"]) }

                // создаем точку
                var new_point = new ymaps.GeoObject({
                    geometry: {
                        type: "Point",
                        coordinates: [order['lat'], order['long']]
                    },
                    properties: {
                        iconContent: order['cluster'] + ": " + order['order_id'],
                        order_id: order['order_id'],
                        selected: false,
                        cluster: order['cluster']
                    }
                }, {
                    preset: cluster_color_mapping[order['cluster']],
                })

                points.push(new_point)
                map_obj.geoObjects.add(new_point)
            }

            $('tbody').sortable({
                update: create_route_on_map
            })

            create_route_on_map()
        }
    });
}


function load_clusters_nums() {
    document.querySelector("#dropdown_cluster_variants").innerHTML = ""

    $.get({
        url: "/admin/get_clusters_nums",
        success: function (result) {
            var clusters = JSON.parse(result)["clusters_nums"]
            for (const i in clusters) {
                var b = document.createElement("button")
                b.innerHTML = clusters[i]
                b.style = "width: 180px"
                b.classList.add("btn")
                b.classList.add("btn-secondary")
                b.onclick = function () {
                    load_orders(clusters[i])
                }
                var l = document.createElement("li")
                l.appendChild(b)
                document.querySelector("#dropdown_cluster_variants").appendChild(l)
            }
        }
    })
}


function create_route_on_map(ev, ui) {
    var rows = $('.sortable-item')
    var new_points = []
    for (var i = 0; i < rows.length; i++) {
        var order_id = rows[i].firstChild.innerHTML
        var point = points.filter((x) => x.properties._data['order_id'] == order_id, points)[0]
        new_points.push(point)
    }

    if (!route_obj) {
        route_obj = new ymaps.multiRouter.MultiRoute({
            referencePoints: new_points
        }, {
            boundsAutoApply: true
        });
        map_obj.geoObjects.add(route_obj);
    } else {
        route_obj.model.setReferencePoints(new_points)
    }
}


$("#yandex_btn").click(
    function(){
        var rows = document.getElementsByTagName("tbody")[0].getElementsByTagName("tr")
        var orders = []
        console.log(rows)
        for (var i = 0; i < rows.length; i++){
            orders.push(rows[i].firstChild.innerHTML)
        }
        if (orders.length > 0){
            $.ajax({
                type: "POST",
                url: "/admin/register_cluster_in_yandex",
                data: JSON.stringify({
                    orders_ids: orders
                }),
                contentType: "application/json",
                success: function(result){
                    var resp = JSON.parse(result)
                    console.log(resp)
                    // var msg = resp['message']
                    if (resp.code != 200){
                        document.getElementById('msg').innerHTML = resp['message']
                    } else {
                        load_orders()
                        document.getElementById('msg').innerHTML = 'Кластер обработан корректно'
                    }
                }
            });
        }
    }
)

load_clusters_nums()
