from db_logic.local_yandex_orders.bd_api_funcs import get_order_by_id as get_order_from_local_db
from db_logic.collect_order_data.compose_info import get_order_full_info


def compose_all_info(order_id):
    local = get_order_from_local_db(order_id)
    gsheets, zippack = get_order_full_info(order_id)

    return local, gsheets, zippack


def create_modules(order_id):
    local, gsheets, zippack = compose_all_info(order_id)

    # делаем базу
    base = {}
    base['comment'] = local['comment']

    # товар
    fake_item = {
        "cost_currency": "RUB",
        "cost_value": local['price'],
        "droppof_point": local['seq_num'],
        "pickup_point": 0,
        "quantity": 1,
        "size": {
            "height": int(local['size'].replace('\\', '/').strip().split('/')[0])/100,
            "length": int(local['size'].replace('\\', '/').strip().split('/')[1]),
            "width": int(local['size'].replace('\\', '/').strip().split('/')[2])
        },
        "title": "набор пакетов",
        "weight": float(local['weight']),
        "fiscalization": {
            "article": "007",
            "supplier_inn": constants['inn'],
            "vat_code_str": "vat0"
        }
    }
