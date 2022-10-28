import json
import phonenumbers
import uuid
import requests


from db_logic.local_yandex_orders.bd_api_funcs import get_order_by_id as get_order_from_local_db
from db_logic.collect_order_data.compose_info import get_order_full_info


with open('constants/yandex_go_constants.json', 'r') as f:
    constants = json.load(f)

with open('tokens/tokens.json', 'r') as tf:
    headers = {
        'Accept-Language': 'ru/ru',
        'Authorization': 'Bearer ' + json.load(tf)['yandex_go']
    }


def compose_all_info(order_id):
    local = get_order_from_local_db(order_id)
    gsheets, zippack = get_order_full_info(order_id)

    return local, gsheets, zippack


def create_modules(order_id):
    # local, gsheets, zippack = compose_all_info(order_id)
    local = get_order_from_local_db(order_id)
    # делаем базу
    base = {}
    base['comment'] = local['comment']

    print(local)

    # товар
    fake_item = {
        "cost_currency": "RUB",
        "cost_value": local['price'],
        "droppof_point": local['seq_num'],
        "pickup_point": 1,
        "quantity": 1,
        "size": {
            "height": int(local['size'].replace('\\', '/').strip().split('/')[0])/100,
            "length": int(local['size'].replace('\\', '/').strip().split('/')[1])/100,
            "width": int(local['size'].replace('\\', '/').strip().split('/')[2])/100
        },
        "title": "набор пакетов",
        "weight": float(local['weight']),
    }
    if not local['paid']:
        fake_item["fiscalization"] = {
            "article": "007",
            "supplier_inn": constants['inn'],
            "vat_code_str": "vat0"
        }

    # точка выгрузки
    address = {
        'comment': local['del_comment'],
        'coordinates': [float(local['long']), float(local['lat'])],
        'fullname': local['fullname']
    }

    contact = {
        'name': local['name'],
        'phone': phonenumbers.format_number(
            phonenumbers.parse(local['phone'], 'RU'), phonenumbers.PhoneNumberFormat().E164)
    }

    external_order_cost = {
        'value': local['price'],
        'currency': 'рубли',
        'currency_sign': 'руб'
    }

    route_point = {
        'address': address,
        'contact': contact,
        'external_order_cost':  external_order_cost,
        'external_order_id': local['order_id'],
        'point_id': local['seq_num'],
        'type': 'destination',
        'visit_order': local['seq_num']
    }

    if not local['paid']:
        route_point['payment_on_delivery'] = {
            'payment_method': 'card'
        }

    return {
        'item': fake_item,
        'route_point': route_point
    }


def generate_post_body(orders_ids_list):

    post_body = {
        'items': [],
        'route_points': [constants['warehouse_route_point']]
    }

    for order_id in orders_ids_list:
        modules = create_modules(order_id)
        post_body['items'].append(modules['item'])
        post_body['route_points'].append(modules['route_point'])

    print(json.dumps(post_body, ensure_ascii=False, indent=4))

    return post_body


def create_yandex_order(orders_ids_list):
    post_body = generate_post_body(orders_ids_list)

    params = {'request_id': uuid.uuid1()}

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/create',
        headers=headers, params=params, data=json.dumps(post_body)
    )
    cont = json.loads(str(resp.content, encoding='utf-8'))

    # try:
    if resp.status_code == 200:
        print('CORRECTLY ADDED')
        # log.info(
        #     f'YANDEX create "{data["order_id"]}":\n    status_code: {resp.status_code}')
        # claim_id, version = cont['id'], cont['version']
        # status = yandex_get_status_after_estimating(claim_id)
        # log.info(
        #     f'YANDEX create "{data["order_id"]}":\n    status: {status}')
        # yandex_write_to_db(order_id=claim_id,
        #                    order_status=status,
        #                    order_version=version)
        # return resp.status_code, ''
    else:
        print('ERROR ADDING', cont['message'], resp.status_code)
        # log.warning(
        #     f'YANDEX create "{data["order_id"]}":\n    status_code: {resp.status_code}\n    msg:{cont["message"]}')
    # except:
        # log.exception()

    return resp.status_code, cont['message']
