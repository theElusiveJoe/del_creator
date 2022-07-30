import requests
import json
import time
import phonenumbers
from ..geocoder.geocoder import address_to_coords


headers = {
    'Accept-Language': 'ru/ru',
    'Authorization': 'Bearer AQAAAABgqYSBAAVM1XuVSQ7EbkGav6KkiZO_puY'
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

    if resp.status_code != 200:
        return 'error'

    cont = json.loads(str(resp.content, encoding='utf-8'))
    print(cont)
    return cont['price']


def yandex_create(data):
    """
    принимает данные формы
    возвращает результат создания заказа
    """

    to_post = json.load(open('api_logic/yandex_constants.json', 'r'))

    to_post = fill_template(to_post, data)

    params = {
        'request_id': data['order_id']
    }

    resp = requests.post(
        f'https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/create',
        headers=headers, params=params, data=json.dumps(to_post)
    )

    cont = json.loads(str(resp.content, encoding='utf-8'))

    if resp.status_code == 200:
        return resp.status_code, cont
        
    print(cont['code'], '-code')
    if resp.status_code == 400 and 'phone' in cont['code']:
        return resp.status_code, 'Введен некорректный телефонный номер'

    return resp.status_code, cont['message']


def fill_template(template, filler):
    route_point = {
        'type': 'destination',
        'visit_order': 2,
        'point_id': 1
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

    return template


if __name__ == '__main__':
    shit = {'order_id': 'aaaaa', 'name': 'NAME', 'phone': '+78005553535', 'city': 'Москва',
            'shortname': 'Тверская 4', 'porch': '', 'door_code': '', 'floor': '', 'flat': '', 'comment': ''}
    yandex_create(shit)
