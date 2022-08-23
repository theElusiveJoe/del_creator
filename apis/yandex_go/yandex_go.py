import requests
import json
import time
import phonenumbers
import os
import sys
from ..geocoder.geocoder import address_to_coords
import logging
import time
import sqlite3


with open(os.path.join(sys.path[0], 'tokens.json'), 'r') as tf:
    headers = {
        'Accept-Language': 'ru/ru',
        'Authorization': 'Bearer ' + json.load(tf)['yandex_go']
    }


def yandex_get_cost(addr, info_from_gsheets):
    """
    принимает на вход данные по заказу
    возвращает цену в рублях
    """

    coordinates = address_to_coords(addr)

    post_body = {
        "items": [
            {
                "quantity": 1,
                "size": {
                    "height": info_from_gsheets['maxlen']/100,
                    "length": info_from_gsheets['midlen']/100,
                    "width": info_from_gsheets['minlen']/100
                },
                "weight": info_from_gsheets['weight']
            }
        ],
        "route_points": [
            {
                "coordinates": [
                    37.592311, 55.801967
                ]
            },
            {
                "coordinates": coordinates
            }
        ]
    }

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v1/check-price', headers=headers, data=json.dumps(post_body))

    cont = json.loads(str(resp.content, encoding='utf-8'))

    if resp.status_code != 200:
        raise Exception()

    return cont['price']


def yandex_create(data, cookies):
    """
    принимает данные формы
    возвращает результат создания заказа
    """

    def fill_template(constants, filler, filler_cookies):
        template = constants['template']
        # 1 создаем точку выгрузки
        route_point = {
            'type': 'destination',
            'visit_order': 2,
            'point_id': 1,
            'payment_on_delivery': {
                'payment_method': 'card'
            },
            'external_order_cost': {
                'value': filler_cookies['yandex_go_cost'],
                'currency': 'рубли',
                'currency_sign': 'руб'
            },
            'external_order_id': filler["order_id"]
        }

        addr_str = filler['fullname']
        route_point['address'] = {
            'coordinates': address_to_coords(addr_str),
            'fullname': addr_str,
        }

        keys = ['porch', 'door_code', 'floor', 'flat', 'comment']
        for key in keys:
            if filler[key] != '':
                route_point[key] = filler[key]

        try:
            phone = phonenumbers.parse(filler['phone'], 'RU')
            phone = phonenumbers.format_number(
                phone, phonenumbers.PhoneNumberFormat().E164)
        except:
            logging.exception('OOPS, failed to parse phone')
            phone = filler['phone']
            print('PHONEEEEEEE', phone)

        route_point['contact'] = {
            'name': filler['name'],
            'phone': filler['phone']
        }

        template['route_points'].append(route_point)

        # 2 создаём фиктивный товар
        fake_item = {
            "cost_currency": "RUB",
            "cost_value": filler_cookies['yandex_go_cost'],
            "droppof_point": 1,
            "pickup_point": 0,
            "quantity": 1,
            "size": {
                "height": int(filler_cookies['min_len'])/100,
                "length": int(filler_cookies['max_len'])/100,
                "width": int(filler_cookies['mid_len'])/100
            },
            "title": "набор пакетов",
            "weight": float(filler_cookies['weight_kg']),
            "fiscalization": {
                "article": "007",
                "supplier_inn": constants['inn'],
                "vat_code_str": "vat0"
            }
        }

        template['items'].append(fake_item)

        template['comment'] = f'ID заказа: {filler["order_id"]}'

        return template

    def yandex_get_status_after_estimating(claim_id):
        status = yandex_get_smth(claim_id, 'status')
        print("➡ status :", status)
        while status == 'estimating' or status == 'new':
            time.sleep(1)
            status = yandex_get_smth(claim_id, 'status')
            print("➡ status :", status)
        return status

    constants = json.load(
        open(os.path.join(sys.path[0], 'constants/yandex_go_constants.json'), 'r'))
    to_post = fill_template(constants=constants,
                            filler=data, filler_cookies=cookies)
    params = {'request_id': data['order_id']}
    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/create',
        headers=headers, params=params, data=json.dumps(to_post)
    )
    cont = json.loads(str(resp.content, encoding='utf-8'))

    try:
        if resp.status_code == 200:
            claim_id, version = cont['id'], cont['version']
            status = yandex_get_status_after_estimating(claim_id)
            print("➡ status :", status)
            yandex_write_to_db(order_id=claim_id,
                                order_status=status)
            return resp.status_code, ''
        else:
            print('RESP STATUS CODE:', resp.status_code)
            print('RESP MESSAGE:', cont['message'])
    except:
        logging.exception()

    if resp.status_code == 400 and 'phone' in cont['code']:
        return resp.status_code, 'Введен некорректный телефонный номер'

    print("➡ cont[message] :", cont['message'])
    return resp.status_code, cont['message']


def yandex_approve(claim_id, version):
    query_params = {
        'claim_id': claim_id
    }
    to_post = {
        'version': version
    }
    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/accept', headers=headers, params=query_params, data=json.dumps(to_post))

    if resp.status_code == 200:
        return

    cont = json.loads(str(resp.content, encoding='utf-8'))
    print(
        f'\nИнформация по заявке{claim_id},\nкод ответа: {resp.status_code}\nрассшифровка: {cont["message"]}')
    raise Exception('Ошибка при одтверждении заявки')


def yandex_get_smth(claim_id, smth=None):
    query_params = {
        'claim_id': claim_id
    }

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/info', headers=headers, params=query_params)

    cont = json.loads(str(resp.content, encoding='utf-8'))

    if resp.status_code != 200:
        logging.critical(
            f'\nИнформация по заявке{claim_id},\nкод ответа: {resp.status_code}\nрассшифровка: {cont["message"]}')

    return cont[smth]


def yandex_write_to_db(order_id, order_status):
    try:
        db_file_path = os.path.join(sys.path[0], 'db.db')
        with open(db_file_path, 'x') as fp:
            pass
    except:
        pass

    with sqlite3.connect(db_file_path) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""CREATE TABLE IF NOT EXISTS yandex_orders(
            id          TEXT PRIMARY KEY,
            status      Text
            );"""
        )
        conn.commit()

        cur.execute(
            f"""INSERT OR IGNORE INTO yandex_orders (id, status)
            VALUES ("{order_id}", "{order_status}");
            """
        )
        print(f'VALUES ("{order_id}", "{order_status}")')
        conn.commit()


def yandex_repeat(claim_id):
    pass


def yandex_performer_position(claim_id):
    query_params = {
        'claim_id': claim_id
    }

    resp = requests.get(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v1/claims/performer-position', headers=headers, params=query_params)

    cont = json.loads(str(resp.content, encoding='utf-8'))

    if resp.status_code != 200:
        logging.critical(
            f'\nИнформация по заявке{claim_id},\nкод ответа: {resp.status_code}\nрассшифровка: {cont["message"]}')

    return cont['position']['lat'], cont['position']['lon']