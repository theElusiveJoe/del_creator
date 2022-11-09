var points
var map_obj;
var route_obj;
var clusters

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


function delete_order(order_i_d){
    $.ajax({
        type: "POST",
        url: "/admin/del_order",
        data: JSON.stringify({
            order_id: order_i_d,
        }),
        contentType: "application/json",
        success: load_orders
    });
}

function click_on_order(order_id) {
    var tr = document.querySelector("#order" + order_id)
    for (var i = 0; i < points.length; i++) {
        if (points[i].properties._data.order_id == order_id) {
            var point = points[i]
            break
        }
    }
    if (point.properties._data.selected) {
        point.options.set("preset", cluster_color_mapping[point.properties._data.cluster])
        tr.className = ""
        point.properties._data.selected = false
    } else {
        point.options.set("preset", cluster_color_mapping['selected'])
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
        zoom: 11
    });
    //    запрашиваем заказы
    $.get({
        url: "/admin/get_unmanaged_orders",
        success: function (result) {
            var orders = JSON.parse(result)['orders']
            orders.sort((a,b) => (a.cluster > b.cluster) ? 1 : -1)
            console.log(orders)

            clusters = [],
            points = [],
            document.querySelector("#total").innerHTML = "Всего заказов: " + orders.length
            document.querySelector("#dropdown_cluster_variants").innerHTML = ""
            // для каждого заказа:
            for (const order of orders) {
                // создаем строчку
                var tr = document.createElement("tr")
                tr.id = 'order'+order["order_id"]
                $("<td>").html(order["cluster"]).appendTo(tr)
                $("<td>").html(order["order_id"]).appendTo(tr)
                $("<td>").html(order["del_time_interval"]).appendTo(tr)
                $("<td>").html(order["fullname"]).appendTo(tr)
                $("<td>").html(order["paid"] ? 'оплачено' : 'не оплачено').appendTo(tr)
                $("<td>").html(order["weight"]).appendTo(tr)
                $("<td>").html(order["positions"]).appendTo(tr)
                $("<td>").html(order["comment"]).appendTo(tr)
                // <th> {% if order['del_service'] != 'yandex': %}
                //     <button onclick="edit_order('{{order["order_id"]}}')"> редактировать </button>
                //     {% endif %}
                // </th>
                var del_btn = document.createElement("button")
                del_btn.innerHTML = "del"
                del_btn.onclick = function(){ delete_order(order['order_id'])}
                var edit_btn = document.createElement("button")
                edit_btn.innerHTML = "edit"
                edit_btn.onclick = function(){edit_order(order['order_id'])}
                var td = document.createElement("td")
                td.append(del_btn)
                tr.append(td)
                var td = document.createElement("td")
                td.append(edit_btn)
                tr.append(td)
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
                    preset: cluster_color_mapping[order['cluster']],
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
            for(const cl_num in clusters){
                var b = document.createElement("button")
                b.innerHTML = clusters[cl_num]
                b.style = "width: 180px"
                b.classList.add("btn")
                b.classList.add("btn-secondary")
                console.log("NEW CLUSTER BUTTON:", clusters[cl_num])
                b.onclick = function (){
                    set_new_cluster(collect_selected_ids(), clusters[cl_num])
                    load_orders()
                }
                var l = document.createElement("li")
                l.appendChild(b)
                document.querySelector("#dropdown_cluster_variants").appendChild(l)
            }

            create_route_on_map()
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

$('.dropdown').hover(function(){ 
    $('.dropdown-toggle', this).trigger('click'); 
  });

$("#drop_claster_button").click(function () {
    set_new_cluster(collect_selected_ids(), 0)
    load_orders()
})

$("#new_claster_button").click(function () {
    var i;
    for (i = 1; i < 14; i++){
        if (! clusters.includes(i)){
            break
        }
    }
    set_new_cluster(collect_selected_ids(), i);
    load_orders()
});

// $("#upd_claster_button").click(
//     () => set_new_cluster(collect_selected_ids(), 0)
// )

function edit_order(order_id) {
    location.href = '/admin/add_order.html?order_id='+order_id+'&protection=False'
}

function create_route_on_map() {
    console.log('Placing points: ', points)
    if (!route_obj) {
        route_obj = new ymaps.multiRouter.MultiRoute({
            referencePoints: points
        }, {
            boundsAutoApply: true
        });
        map_obj.geoObjects.add(route_obj);
    } else {
        route_obj.model.setReferencePoints(points)
    }
}

ymaps.ready(load_orders)