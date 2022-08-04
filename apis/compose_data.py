import json
from .yandex_go.yandex_go import yandex_get_cost
# from .dostavista_api import dostavista_get_cost


def count_delivery(addr, info_from_gsheets):
    """
    Принимает на вход строку с адресом
    Возвращает словарь {
        <сервис>: <цена>
        }
    """
    ret = []
    
    try:
        yandex_cost = yandex_get_cost(addr, info_from_gsheets)
        ret.append({
            'label': 'Яндекс GO',
            'cost': yandex_cost,
            'url': '/yandex_form.html',
            'name': 'yandex_go'
        })
    except:
        logging.exception(f'Ошибка yandex_get_cost({addr}, info_from_gsheets)')

    return ret
