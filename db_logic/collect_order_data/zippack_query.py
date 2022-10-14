import logging

import requests
import json

with open('tokens/tokens.json', 'r') as f:
    TOKEN = json.load(f)['zippack_token']

def get_order_from_zippack(order_id):
    query_params = {
        'apikey': TOKEN
    }
    resp = requests.get(f'https://zippack.ru/api/order/get/{order_id}', params=query_params)
    try:
        cont = json.loads(str(resp.content, encoding='utf-8'))
        if resp.status_code != 200:
            logging.critical(f'\nИнформация по заявке{claim_id},\nкод ответа: {resp.status_code}\nрассшифровка: {cont["message"]}')
            raise Exception
        return cont
    except:
        logging.exception('проблемы с зиппаком')
        raise Exception