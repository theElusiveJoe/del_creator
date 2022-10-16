import pandas as pd
import logging
import sys
import json

handler = logging.StreamHandler(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)

with open('tokens/tokens.json', 'r') as tf:
    csv_link = json.load(tf)['gsheets']['csv_link']


def download_order_row(order_id):
    log.info(f'GSHEETS get_line "{order_id}"')
    table = pd.read_csv(csv_link, header=1, usecols=[x for x in range(19)]).rename(
        columns={'Число': 'date',
                 'Заказ': 'id',
                 'Номер счета': 'account_number',
                 'Нал': 'cache',
                 'Безнал': 'emoney',
                 'Оплачено (число)': 'paid',
                 'Форма оплаты': 'payment_method',
                 'Время': 'payment_time',
                 'Примечание': 'comment',
                 'Вывоз': 'delivery_service',
                 'Письмо на склад': 'mail_on_warehouse',
                 'Доставка на': 'delivery_arranged_on',
                 'Мест': 'positions',
                 'габариты': 'size',
                 'вес': 'weight',
                 'Списано со склада': 'decommisioned',
                 'Статус': 'status',
                 'примечания': 'comment2',
                 'warehouse': 'warehouse'})
    row = table[table['id'] == order_id].iloc[0].fillna('').to_dict()
    row['emoney'] = ''.join(filter(lambda x: ord(x) < 100, row['emoney'])).replace(' ', '')
    row['cache'] = ''.join(filter(lambda x: ord(x) < 100, row['cache'])).replace(' ', '')
    row['paid'] = row['paid'] == 'оплачено'
    log.info(row['emoney'])
    return row




def get_order_line_from_ghseets(order_id):
    try:
        return download_order_row(order_id)
    except Exception:
        log.warning(f'GSHEETS get_line "{order_id}" - error')
        raise Exception('Проблемы с гугл таблицей')