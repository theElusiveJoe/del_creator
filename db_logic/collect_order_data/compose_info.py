import re
import logging
import sys
import json

from db_logic.collect_order_data.gsheets_as_csv import get_order_line_from_ghseets
from db_logic.collect_order_data.zippack_query import get_order_from_zippack
from db_logic.collect_order_data.mail_reader import get_order_from_mail

handler = logging.StreamHandler(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)


def get_order_full_info(order_id):
    row = get_order_line_from_ghseets(order_id.strip())
    if ord('A') <= ord(order_id.strip()[0]) <= ord('Z'):
        try:
            return row, get_order_from_zippack(re.sub("\D", "", order_id))
        except Exception:
            log.exception('')
            log.error('Проблема с зиппаком')
    else:
        try:
             return row, get_order_from_mail(order_id)
        except Exception:
            log.exception('')
            log.error('Проблема с почтой')

def get_order_line_from_ghseets_for_yandex_user(order_id):
    try:
        row = get_order_line_from_ghseets(order_id)
        if row['габариты']:
            gabs = (
                sorted(list(map(int, row['габариты'].strip().replace('\\', '/').split('/')))))
        else:
            gabs = [0.5, 0.5, 0.5]
        ret = {
            'id': row.name.strip(),
            'weight': float(row['вес'].strip().replace(',', '.')) if 'вес' in row else 0.1,
            'maxlen': gabs[2],
            'midlen': gabs[1],
            'minlen': gabs[0]
        }
        log.info(f'GSHEETS get_line "{order_id}" - correct')
        return ret
    except Exception:
        log.warning(f'GSHEETS get_line "{order_id}" - error')
        raise Exception('Проблемы с гугл таблицей')

def get_order_info_for_local_order(order_id):
    gsheets_info, shop_info = get_order_full_info(order_id)

    print(json.dumps(gsheets_info, indent=4, ensure_ascii=False))
    print(json.dumps(shop_info, indent=4, ensure_ascii=False))
    shop_info = shop_info['obj']
    result = dict()

    result['order_id'] = gsheets_info['id']
    result['pay_type'] = gsheets_info['payment_method']
    result['cache'] = gsheets_info['cache']
    result['emoney'] = gsheets_info['emoney']
    result['comment'] = gsheets_info['comment']
    result['paid'] = gsheets_info['paid']

    customer = shop_info['Customer']
    log.info(customer.get('Organisation'))
    result['name'] = ' '.join(map(str, (filter(None, [customer['FirstName'], customer['LastName'], customer.get('Organisation')]))))
    result['phone'] = customer['Phone']

    result['fullname'] = ' '.join([customer['Region'], customer['District'], customer['City'],customer['Street'],customer['House'],customer['Structure'],customer['CustomField1'],]).strip()
    result['del_comment'] = ''
    result['del_comment'] += 'квартира/офис ' + customer['Apartment'].strip() if customer['Apartment'].strip() != '' else ''
    result['del_comment'] += 'этаж ' + customer['Floor'].strip() if customer['Floor'].strip() != '' else ''
    result['del_comment'] += 'подъезд/вход ' + customer['Entrance'].strip() if customer['Entrance'].strip() != '' else ''

    return result



