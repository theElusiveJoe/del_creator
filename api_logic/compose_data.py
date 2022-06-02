import json
from .y_api import yandex_get_cost


def count_delivery(addr, info_from_gsheets):
    """
    Принимает на вход строку с адресом
    Возвращает словарь {
        <сервис>: <цена>
        }
    """
    return {
        'Яндекс GO' : [yandex_get_cost(addr, info_from_gsheets), '/yandex_form.html']
    }