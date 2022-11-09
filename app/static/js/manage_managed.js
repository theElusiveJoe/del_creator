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
    $(document).ready(function(){
        $('#myTable').dataTable();
    });
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
    $(document).ready(function(){
        $('#myTable').dataTable();
    });
}




function get_invoice(order_id) {
    var link = document.createElement('a')
    link.setAttribute('href', '/admin/get_invoice/'+order_id)
    link.setAttribute('target', '_blank')
    link.click()
}