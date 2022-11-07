import json
import phonenumbers
import uuid
import requests
import time


from db_logic.local_yandex_orders.bd_api_funcs import get_order_by_id as get_order_from_local_db
from db_logic.collect_order_data.compose_info import get_order_full_info


with open('constants/yandex_go_constants.json', 'r') as f:
    constants = json.load(f)

with open('tokens/tokens.json', 'r') as tf:
    headers = {
        'Accept-Language': 'ru/ru',
        'Authorization': 'Bearer ' + json.load(tf)['yandex_go']
    }


def get_smth(claim_id, smth=None):
    query_params = {
        'claim_id': claim_id
    }

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/info', headers=headers, params=query_params)

    cont = json.loads(str(resp.content, encoding='utf-8'))

    # if resp.status_code != 200:
    #     logging.critical(
    #         f'\nИнформация по заявке{claim_id},\nкод ответа: {resp.status_code}\nрассшифровка: {cont["message"]}')

    return cont[smth], cont['version']


def approve(claim_id, version):
    query_params = {
        'claim_id': claim_id
    }
    to_post = {
        'version': version
    }
    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/accept', headers=headers, params=query_params, data=json.dumps(to_post))

    if resp.status_code == 200:
        return 200, 'all ok'

    cont = json.loads(str(resp.content, encoding='utf-8'))
    return resp.status_code, cont['message']


def cancel_yandex_order(claim_id):
    query_params = {
        'claim_id': claim_id
    }
    to_post = {
        'version': 1,
        'cancel_state': 'free'
    }
    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/cancel', headers=headers, params=query_params, data=json.dumps(to_post))

    if resp.status_code == 200:
        return 200, 'all ok'

    cont = json.loads(str(resp.content, encoding='utf-8'))
    return resp.status_code, cont['message']



def get_status_after_estimating(claim_id):
    status, version = get_smth(claim_id, 'status')
    while status == 'estimating' or status == 'new':
        time.sleep(1)
        status, version = get_smth(claim_id, 'status')
    return status, version


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
            "height": local['size_x'],
            "length": local['size_y'],
            "width": local['size_z']
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
        'coordinates': [local['long'], local['lat']],
        'fullname': local['fullname']
    }

    contact = {
        'name': local['name'],
        'phone': local['phone']
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
        'visit_order': local['seq_num'],
        'skip_confirmation': True
    }

    if not local['paid']:
        route_point['payment_on_delivery'] = {
            'payment_method': 'card'
        }

    return {
        'item': fake_item,
        'route_point': route_point
    }


def create_post_body(orders_ids_list):

    post_body = {
        'items': [],
        'route_points': [constants['warehouse_route_point']],
        'emergency_contact': constants['emergency_contact'],
    }

    for order_id in orders_ids_list:
        modules = create_modules(order_id)
        post_body['items'].append(modules['item'])
        post_body['route_points'].append(modules['route_point'])

    print(json.dumps(post_body, ensure_ascii=False, indent=4))

    return post_body


def create_yandex_order(orders_ids_list):
    post_body = create_post_body(orders_ids_list)

    params = {'request_id': uuid.uuid1()}

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/create',
        headers=headers, params=params, data=json.dumps(post_body)
    )
    cont = json.loads(str(resp.content, encoding='utf-8'))

    if resp.status_code == 200:
        print('CORRECTLY ADDED')
        claim_id = cont['id']
        status, version = get_status_after_estimating(claim_id)
        # return approve(claim_id, version)
        return 200, None, cont['id']
    print('ERROR ADDING', cont['message'], resp.status_code)
    return resp.status_code, cont['message'], None
