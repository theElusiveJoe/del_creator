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
    return [
        {
            'label': 'Яндекс GO',
            'cost': yandex_get_cost(addr, info_from_gsheets),
            'url': '/yandex_form.html',
            'name' : 'yandex_go'
        },

    ]
