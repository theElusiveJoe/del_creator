function drop_order(order_id) {
    $.post({
        url: "/admin/drop_managed",
        data: {
            "order_id": order_id
        },
        success: function (result) {
            window.location.reload(true)
        }
    })
}

function pop_from_managed(order_id) {
    $.post({
        url: "/admin/pop_from_managed",
        data: {
            "order_id": order_id
        },
        success: function (result) {
            window.location.reload(true)
        }
    })
}


function edit_order(order_id) {
    location.href = '/admin/add_order.html?order_id='+order_id+'&protection=False'
}