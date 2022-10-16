from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, request

from db_logic.collect_order_data.compose_info import get_order_info_for_local_order
from db_logic.local_yandex_orders.bd_api_funcs import add_order as add_order_to_local_bd

import logging
import sys
import json
import os
import hashlib

handler = logging.StreamHandler(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)

with open(os.path.join(sys.path[0], 'tokens/tokens.json'), 'r') as tokens:
    tokens = json.load(tokens)
    password = tokens['hashed_password']
    ymaps_token = tokens['msk_ymaps']


bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return render_template('admin/admin_panel.html')

    if request.method == 'GET':
        return render_template('admin/login.html')

    if hashlib.md5(request.form['password'].encode()).hexdigest() == password:
        session['logged_in'] = True
        return render_template('admin/admin_panel.html')
    else:
        return render_template('admin/login.html', failed=True)

@bp.route('/add_order.html', methods=['GET', 'POST'])
def add_order_raw():
    if not session.get('logged_in'):
        redirect('/login.html')

    if request.method == 'GET':
        if not request.args.get('order_id'):
            return render_template('admin/add_order.html', raw=True)

        primary_info = get_order_info_for_local_order(request.args.get('order_id').strip())
        log.info(primary_info)

        return render_template('admin/add_order.html', raw=False, primary_info=primary_info, ymaps_token=ymaps_token)

    if request.method == 'POST':
        print(json.dumps(dict(request.form), ensure_ascii=False, indent=4))
        add_order_to_local_bd(form=request.form)
        return 'Добавлено!'

    # 1. получаем инфу по заказу из бд и гугл-табличкиjkj


    # 2. рендерим шаблон создания, заполняя его всяким
    # return render_template('/adь min/input_order_num.html')

    # иначе закидываем в бд результат
