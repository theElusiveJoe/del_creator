from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, request

from db_logic.collect_order_data.compose_info import get_order_info_for_local_order
from db_logic.collect_order_data.compose_info import get_order_line_from_ghseets
from db_logic.local_yandex_orders.bd_api_funcs import add_order as add_order_to_local_db
from db_logic.local_yandex_orders.bd_api_funcs import get_orders as get_orders_from_local_db
from db_logic.local_yandex_orders.bd_api_funcs import upd_cluster as upd_cluster_in_local_db
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



# @bp.route('/admin_panel.html')
@bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return render_template('admin/admin_panel.html')

    if request.method == 'GET':
        return render_template('admin/login.html')

    if hashlib.md5(request.form['password'].encode()).hexdigest() == password:
        session['logged_in'] = True
        return render_template('admin/manage_orders.html')
    else:
        return render_template('admin/login.html', failed=True)


@bp.route('/add_order.html', methods=['GET', 'POST'])
def add_order_raw():
    if not session.get('logged_in'):
        return render_template('/admin/login.html')

    if request.method == 'GET':
        if not request.args.get('order_id'):
            return render_template('admin/add_order.html', raw=True)

        primary_info, session['last_order_id'], session['last_order_gsheets_info'], session['last_order_shop_info'] = get_order_info_for_local_order(
            request.args.get('order_id').strip())
        log.info(primary_info)

        return render_template('admin/add_order.html', raw=False, primary_info=primary_info, ymaps_token=ymaps_token)

    if request.method == 'POST':
        print(json.dumps(dict(request.form), ensure_ascii=False, indent=4))
        request_order_id = request.form['order_id']
        if 'last_order_id' in session.keys() and request_order_id == session['last_order_id']:
            print('CACHING WORKED')
            add_order_to_local_db(
                form=request.form, gsheets=session['last_order_gsheets_info'])
        else:
            add_order_to_local_db(
                form=request.form, gsheets=get_order_line_from_ghseets(request_order_id))

        return render_template('admin/add_order.html', raw=True)


@bp.route('/manage_orders.html', methods=['GET', 'POST'])
def manage_orders():
    if not session.get('logged_in'):
        return render_template('/admin/login.html')

    if request.method == 'GET':
        return render_template('admin/manage_orders.html', ymaps_token=ymaps_token)


@bp.route('/get_orders', methods=['GET'])
def get_orders():
    if not session.get('logged_in'):
        return redirect('/admin/login.html')

    orders = get_orders_from_local_db()
    return json.dumps({'orders': orders}, ensure_ascii=False)


@bp.route('/update_cluster', methods=['POST'])
def upd_cluster():
    request.json
    upd_cluster_in_local_db(request.json['orders_ids'], request.json['new_cluster_num'])
    return 'lol'