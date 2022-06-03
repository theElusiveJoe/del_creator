import requests
import json


def address_to_coords(address, results_max_num=1):
    headers = {
        'apikey': '7428d35f-cc5a-4ad4-92d8-76f19f0af700',
        'geocode': address,
        'format' : 'json',
        'results': results_max_num
    }

    resp = requests.get(
        f'https://geocode-maps.yandex.ru/1.x/', params=headers)

    if resp.status_code != 200:
        raise Exception('Geocode responce error')

    try:
        cont = json.loads(str(resp.content, encoding='utf-8'))
        coords = (cont['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split())
    except:
        raise Exception('Parsing geocode responce')

    return [float(coords[0]), float(coords[1])]


if __name__ == '__main__':
   print(address_to_coords('Тверская 6'))