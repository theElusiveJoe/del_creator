

  $("#get_orders_btn").click(function () {
    $.get({
        url: "/admin/get_orders",
            success: function (result) {
                var orders = JSON.parse(result)['orders']

                for (const order of orders){
                    new_point = new ymaps.GeoObject({
                        geometry: {
                            type: "Point",
                            coordinates: [order['lat'], order['long']]
                        },
                        properties: {
                            iconContent: order['order_id'],
                        }
                    },{
                        preset: 'islands#blackStretchyIcon',
                    })

                    map_obj.geoObjects.add(new_point)
                }
            }
  });
});