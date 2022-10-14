from apis.yandex_go_user.yandex_go import yandex_get_cost
# from .dostavista_api import dostavista_get_cost


def get_services_prices(addr, info_from_gsheets):
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
