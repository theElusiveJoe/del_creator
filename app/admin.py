from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, request

from db_logic.collect_order_data.compose_info import get_order_info_for_local_order

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
    password = json.load(tokens)['hashed_password']


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
            return render_template('admin/add_order.html')

        primary_info = get_order_info_for_local_order(request.args.get('order_id').strip())
        log.info(primary_info)

    return 'add_prder_by_num'



    # 1. получаем инфу по заказу из бд и гугл-табличкиjkj


    # 2. рендерим шаблон создания, заполняя его всяким
    # return render_template('/adь min/input_order_num.html')

    # иначе закидываем в бд результат
