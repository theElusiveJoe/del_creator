import requests
import json
import phonenumbers
import time
import os, sys

with open(os.path.join(sys.path[0], 'tokens.json'), 'r') as tf:
    headers = {
        "X-DV-Auth-Token" : json.load(tf)['dostavista']
    }


def dostavista_get_cost(addr, info_from_gsheets):
    post_body = {
        "matter" : "набор пакетов",
        "type" : "same_day",
        "total_weight_kg" : info_from_gsheets['weight'],
        "points" : [
            {
                "address" : "Москва, Складочная улица, 1с13"
            },
            {
                "address" : addr
            }

        ]
    }

    resp = requests.post(
        f'https://robotapitest.dostavista.ru/api/business/1.1/calculate-order',
        headers = headers,
        data = json.dumps(post_body)
    )

    if resp.status_code != 200:
        print('STATUS CODE:', resp.status_code)
        print(str(resp.content, encoding='utf-8'))
        return 'error'

    cont = json.loads(str(resp.content, encoding='utf-8'))
    # print(str(resp.content, encoding='utf-8'))

    if cont['is_successful'] == True:
        return cont['order']['delivery_fee_amount']
    else:
        return 'error'
         

def dostavista_create(data, cookies):
    post_body = json.load(open(os.path.join(sys.path[0],'api_logic/dostavista_constants.json'), 'r'))

    try:
        phone = phonenumbers.parse(data['phone'], 'RU')
        phone = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat().E164)
        data[phone] = phone
    except:
        return 400, 'Некорректно введен телефон'

    post_body = fill_template(post_body, data, cookies)

    print(post_body)

    resp = requests.post(
        f'https://robotapitest.dostavista.ru/api/business/1.1/create-order',
        headers = headers,
        data = json.dumps(post_body)
    )

    cont = json.loads(str(resp.content, encoding='utf-8'))
    
    if resp.status_code != 200:
        print('STATUS CODE:', resp.status_code)
        print('RESPONCE', cont)
        return resp.status_code, cont['errors'] 

    if cont['is_successful'] == True:
        return resp.status_code, cont['order']['delivery_fee_amount']
    else:
        return resp.status_code, cont['errors']


def dostavista_intervals():
    resp = requests.get(
        f'https://robotapitest.dostavista.ru/api/business/1.1/delivery-intervals',
        headers = headers
    )

    cont = json.loads(str(resp.content, encoding='utf-8'))

    intervals = []

    templ = '%Y-%m-%dT%H:%M:%S+03:00'
    for inter in cont['delivery_intervals']:
        a = time.strptime(inter['required_start_datetime'], templ)
        b = time.strptime(inter['required_finish_datetime'], templ)
        intervals.append([inter['required_start_datetime'] , inter['required_finish_datetime'], f'{a.tm_hour}:00 - {b.tm_hour}:00'])

    return intervals


def fill_template(template, filler, cookies):
    route_point = {
        "contact_person": {
            "phone" : filler['phone'],
            "name" : filler["name"]
        },
        "client_order_id" : filler["order_id"],
        "required_start_datetime" : filler['required_datetime'].split()[0],
        "required_finish_datetime" : filler['required_datetime'].split()[1]
    }

    for x in ["address", "entrance_number", "intercom_code", "floor_number", "apartment_number", "invisible_mile_navigation_instructions"]:
        if filler[x] != '':
            route_point[x] = filler[x]

    template['points'].append(route_point)
    template['total_weight_kg'] = cookies['weight_kg']

    return template


if __name__ == '__main__':
    dostavista_intervals()