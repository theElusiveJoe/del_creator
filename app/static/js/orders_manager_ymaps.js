var points
var map_obj;
var clusters

var cluster_color_mapping = {
    // для нулевого кластера
    0: 'islands#grayStretchyIcon',
    // для выделенных
    15: 'islands#redStretchyIcon',
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


function click_on_order(order_id) {
    var tr = document.querySelector("#" + order_id)
    for (var i = 0; i < points.length; i++) {
        if (points[i].properties._data.order_id == order_id) {
            var point = points[i]
            break
        }
    }
    if (point.properties._data.selected) {
        point.options.set("preset", "islands#blackStretchyIcon")
        tr.className = ""
        point.properties._data.selected = false
    } else {
        point.options.set("preset", "islands#blueStretchyIcon")
        tr.className = "table-primary"
        point.properties._data.selected = true
    }
}

function load_orders() {
    //    обновляем карту
    document.querySelector("#orders_list").innerHTML = ''
    if (!!map_obj) {
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
            
            clusters = [],
            points = []
            // для каждого заказа:
            for (const order of orders) {
                // создаем строчку
                var tr = document.createElement("tr")
                tr.id = order["order_id"]
                $("<td>").html(order["cluster"]).appendTo(tr)
                $("<td>").html(order["order_id"]).appendTo(tr)
                $("<td>").html(order["del_time_interval"]).appendTo(tr)
                $("<td>").html(order["weight"]).appendTo(tr)
                $("<td>").html(order["positions"]).appendTo(tr)
                $("<td>").html(order["comment"]).appendTo(tr)
                document.querySelector("#orders_list").appendChild(tr)
                tr.onclick = function () { click_on_order(order["order_id"]) }

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
                    preset: 'islands#blackStretchyIcon',
                })

                // событие клика по точке
                points.push(new_point)
                new_point.events.add('click', function (e) {
                    var target = e.get('target');
                    var order_id = target.properties.get("order_id")
                    click_on_order(order_id)
                })
                if (!clusters.includes(parseInt(order['Cluster']))) {
                    clusters.push(parseInt(order['cluster']))
                }
                // добавляем точку на карту
                map_obj.geoObjects.add(new_point)
            }
            clusters =  [...new Set(clusters)]
            clusters.sort()
            console.log('Clusters:', clusters)
            console.log('Points:', points)
        }
    });
}


function collect_selected_ids() {
    selected_points_ids = []
    for (var i = 0; i < points.length; i++) {
        if (points[i].properties._data.selected) {
            selected_points_ids.push((points[i].properties._data.order_id))
        }
    }
    console.log('Selected:', selected_points_ids)
    return selected_points_ids
}

function set_new_cluster(selected_ids, new_cluster_num) {
    $.ajax({
        type: "POST",
        url: "/admin/update_cluster",
        data: JSON.stringify({
            orders_ids: selected_ids,
            new_cluster_num: new_cluster_num
        }),
        // success: success,
        contentType: "application/json"
    });
}


$("#drop_claster_button").click(function () {
    set_new_cluster(collect_selected_ids(), 0)
    load_orders()
})

$("#new_claster_button").click(function () {
    var i = 1;
    for (; i < clusters.length; i++) {
        if (clusters[i] - clusters[i - 1] > 1) {
            break
        }
    }
    set_new_cluster(collect_selected_ids(), clusters[i - 1]+1);
    load_orders()
});

// $("#upd_claster_button").click(
//     () => set_new_cluster(collect_selected_ids(), 0)
// )

ymaps.ready(load_orders)