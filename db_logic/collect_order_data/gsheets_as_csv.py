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
    def to_int(rawstr):
        res = ''.join(filter(lambda x: ord(x) < 100, rawstr)).replace(' ', '')
        return res

    log.info(f'GSHEETS get_line "{order_id}"')
    table = pd.read_csv(csv_link, header=1, usecols=[x for x in range(19)]).rename(
        columns={'Число': 'date',
                 'Заказ': 'id',
                 'Номер счета': 'account_number',
                 'Нал': 'cache',
                 'Безнал': 'emoney',
                 'Оплачено (число)': 'paid',
                 'Форма оплаты': 'payment_method',
                 'Время': 'del_time_interval',
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
    print('LOOOOOKING FOR', order_id)
    row = table[(table['id'] == order_id ) | (table['account_number'] == order_id)].iloc[0].fillna('').to_dict()
    row['emoney'] = to_int(row['emoney'])
    row['cache'] = to_int(row['cache'])
    row['paid'] = row['paid'] == 'оплачено'
    row['positions'] = to_int(row['positions']) if len(row['positions']) > 0 else 0
    if row['id'] == '':
        row['id'] = row['account_number']
    print(row)
    return row


def get_order_line_from_ghseets(order_id):
    try:
        row = download_order_row(order_id)
        return row, row['id'] == row['account_number']
    except Exception:
        log.warning(f'GSHEETS get_line "{order_id}" - error')
        raise Exception('Проблемы с гугл таблицей')