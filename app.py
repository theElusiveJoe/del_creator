from flask import Flask, render_template, request, make_response

from api_logic.compose_data import count_delivery
from api_logic.y_api import yandex_create

from db_logic.gsheets_query import get_order_info_from_gsheetstring

import json

import logging

app = Flask(__name__)
ymaps_api_key = ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', ymaps_token=ymaps_api_key)

    # считаем примерные цены доставок
    info_from_gsheets = get_order_info_from_gsheetstring(request.form['stringnum'])
    delivery_prices = count_delivery(request.form['fullname'], info_from_gsheets)

    res = make_response(render_template('choose_service.html', price_dict=delivery_prices))
    res.set_cookie("fullname", request.form['fullname'])
    res.set_cookie('order_id', info_from_gsheets['id'])
    return res


@app.route('/yandex_form.html', methods=['GET', 'POST'])
def yandex_form():
    # если это метод GET, то просто возвращаем страничку
    if request.method == 'GET':
        return render_template('yandex_form.html', 
        cook=request.cookies, ymaps_token=ymaps_api_key)

    # если же это POST, то пытаемся сздать заказ
    try:
        code, cont = yandex_create(request.form)
    except:
        # это потом переделать
        logging.exception('Произошла ошибка при создании заказа yandex go')
        return 'error occured'

    # создаем ответ
    res = make_response()
    
    # в куки ответа записываем все, что ввел клиент
    for x in request.form:
        res.set_cookie(x, request.form[x])
    # если удалось создать заказ, то выдаем страничку с успехом
    if code == 200:
        res.response = render_template('order_created.html')
        return res

    # если не удалось создать заявку, то возвращаем страничку с формой, 
    # но заполняем ее сообщением об ошибке и тем, что навводил клиент
    res = make_response(render_template('yandex_form.html', cook=request.form, errors=cont, ymaps_token=ymaps_api_key))    

    return res

if __name__ == '__main__':
    with open('tokens.json', 'r') as tokens:
        ymaps_api_key = json.load(tokens)['msk_ymaps']

    app.run(debug=True)