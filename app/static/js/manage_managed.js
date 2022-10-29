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