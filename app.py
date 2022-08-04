from flask import Flask, render_template, request, make_response

from apis.compose_data import count_delivery
from apis.yandex_go.yandex_go import yandex_create


from db_logic.gsheets_query import get_order_info_from_gsheetstring
from db_logic.gsheets_as_csv import get_order_line_from_ghseets
import json

import logging


with open('tokens.json', 'r') as tokens:
    tokens = json.load(tokens)

app = Flask(__name__)
ymaps_api_key = ""


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', ymaps_token=ymaps_api_key)

    try:
        info_from_gsheets = get_order_line_from_ghseets(
            request.form['stringnum'].strip())
    except:
        logging.exception(
            f'Ошибка гугл таблиц: {request.form["stringnum"].strip()}')
        return render_template('error_occured.html',
                               error_reason='Проблема с базой данных или гугл таблицами',
                               order_id=request.form['stringnum'].strip(),
                               recomendation='Пожалуйста, проверьте, правильно ли вы ввели id заказа. Если id верный, свяжитесь с менеджером и сообщите причину ошибки.')

    try:
        delivery_prices = count_delivery(
            request.form['address'], info_from_gsheets)
        if not delivery_prices:
            raise Exception('Не удалось рассчитать доставку ни одним сервисом')
    except:
        logging.exception(
            f'Ошибка рассчёта стоимости: {request.form["stringnum"].strip()}')
        return render_template('error_occured.html',
                               error_reason='Не удалось получить стоимость доставки ни от одного сервиса',
                               recomendation=f'Проверьте правильность адреса: {request.form["address"]}',
                               order_id=request.form['stringnum'].strip())

    res = make_response(render_template(
        'choose_service.html', price_dict=delivery_prices))
    for service in delivery_prices:
        res.set_cookie(service['name'] + '_cost', service['cost'])
    res.set_cookie('yandex_delivery')
    res.set_cookie("weight_kg", str(info_from_gsheets['weight']))
    res.set_cookie("min_len", str(info_from_gsheets['minlen']))
    res.set_cookie("mid_len", str(info_from_gsheets['midlen']))
    res.set_cookie("max_len", str(info_from_gsheets['maxlen']))
    res.set_cookie("address", request.form['address'])
    res.set_cookie("fullname", request.form['address'])
    res.set_cookie('order_id', info_from_gsheets['id'])

    return res


@app.route('/yandex_form.html', methods=['GET', 'POST'])
def yandex_form():
    # если это метод GET, то просто возвращаем страничку
    if request.method == 'GET':
        return render_template('yandex_form.html',
                               cook=request.cookies, ymaps_token=tokens['msk_ymaps'])

    # если же это POST, то пытаемся сздать заказ
    try:
        code, cont = yandex_create(data=request.form, cookies=request.cookies)
    except:
        # это потом переделать
        logging.exception('Произошла ошибка при создании заказа яндекс go')
        return 'Произошла внутренняя ошибка. Пожалуйста, свяжитесь с менеджером'

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
    res = make_response(render_template('yandex_form.html', cook=request.form,
                        errors='ПРОИЗОШЛА ОШИБКА: '+cont, ymaps_token=ymaps_api_key))

    return res


@app.route('/dostavista_form.html', methods=['GET', 'POST'])
def dostavista_form():
    if request.method == 'GET':
        return render_template('dostavista_form.html',
                               cook=request.cookies,
                               intervals=dostavista_intervals())

    try:
        code, cont = dostavista_create(request.form, request.cookies)
    except:
        # это потом переделать
        logging.exception('Произошла ошибка при создании заказа dostavista')
        return 'error occured'

    # если удалось создать заказ, то выдаем страничку с успехом
    if code == 200:
        # создаем ответ
        res = make_response()
        # в куки ответа записываем все, что ввел клиент
        for x in request.form:
            res.set_cookie(x, request.form[x])
        res.response = render_template('order_created.html')
        return res

    # если не удалось создать заявку, то возвращаем страничку с формой,
    # но заполняем ее сообщением об ошибке и тем, что навводил клиент
    res = make_response(render_template('dostavista_form.html',
                        cook=request.form, errors=cont, intervals=dostavista_intervals()))
    for x in request.form:
        res.set_cookie(x, request.form[x])
    return res


if __name__ == '__main__':
    app.run(debug=True)
