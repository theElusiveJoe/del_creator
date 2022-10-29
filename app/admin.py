from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, request

from db_logic.collect_order_data.compose_info import get_order_info_for_local_order
from db_logic.collect_order_data.compose_info import get_order_line_from_ghseets

import db_logic.local_yandex_orders.bd_api_funcs as local_db
from apis.yandex_go_corp.yandex_go_corp import create_yandex_order
from apis.create_invoice.create_invoice import create_invoice_file

import logging
import sys
import json
import os
import hashlib
import phonenumbers
import uuid

handler = logging.StreamHandler(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)

with open(os.path.join(sys.path[0], 'tokens/tokens.json'), 'r') as tokens:
    tokens = json.load(tokens)
    password = tokens['hashed_password']
    ymaps_token = tokens['msk_ymaps']

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@bp.route('/admin_panel.html')
@bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return render_template('/admin/admin_panel.html')

    if request.method == 'GET':
        return render_template('/admin/login.html')

    if hashlib.md5(request.form['password'].encode()).hexdigest() == password:
        session['logged_in'] = True
        return render_template('/admin/manage_orders.html')
    else:
        return render_template('/admin/login.html', failed=True)


@bp.route('/add_order.html', methods=['GET', 'POST'])
def add_order_raw():
    # if not session.get('logged_in'):
    #     return render_template('/admin/login.html')

    if request.method == 'GET':
        if not request.args.get('order_id'):
            return render_template('/admin/add_order.html', raw=True)

        primary_info, session['last_order_id'], session['last_order_gsheets_info'], session[
            'last_order_shop_info'] = get_order_info_for_local_order(
            request.args.get('order_id').strip())
        log.info(primary_info)

        return render_template('/admin/add_order.html', raw=False, primary_info=primary_info, ymaps_token=ymaps_token)

    if request.method == 'POST':
        request_order_id = request.form['order_id']
        form = dict(request.form)

        # if 'last_order_id' in session.keys() and request_order_id == session['last_order_id']:
        #     print('CACHING WORKED')
        #     add_order_to_local_db(
        #         form=request.form, gsheets=session['last_order_gsheets_info'])
        # else:
        err_msg = local_db.add_order(
            form=form, gsheets=get_order_line_from_ghseets(request_order_id))

        if err_msg:
            primary_info, _, _, _ = get_order_info_for_local_order(
                request_order_id)
            return render_template('/admin/add_order.html', raw=False, primary_info=primary_info,
                                   ymaps_token=ymaps_token, err_msg=err_msg)

        return render_template('/admin/add_order.html', raw=True)


@bp.route('/manage_orders.html', methods=['GET', 'POST'])
def manage_orders():
    # if not session.get('logged_in'):
    #     return render_template('/admin/login.html')

    if request.method == 'GET':
        return render_template('/admin/manage_orders.html', ymaps_token=ymaps_token)


@bp.route('/manage_cluster.html', methods=['GET', 'POST'])
def manage_clusters():
    # if not session.get('logged_in'):
    # return render_template('/admin/login.html')

    if request.method == 'GET':
        return render_template('/admin/manage_clusters.html', ymaps_token=ymaps_token)


@bp.route('/get_unmanaged_orders', methods=['GET'])
def get_unamanaged_orders():
    orders = local_db.get_unmanaged_orders()
    print('ORDEEEEEEEEEEEEEEEEEERS', orders)
    return json.dumps({'orders': orders}, ensure_ascii=False)


@bp.route('/get_orders_by_cluster', methods=['GET'])
def get_orders_by_cluster():
    cl_num = request.args.get('cluster_num')
    orders = local_db.get_orders_by_cluster(cl_num)
    return json.dumps({'orders': orders}, ensure_ascii=False)


@bp.route('/get_clusters_nums', methods=['GET'])
def get_clusters_nums():
    # if not session.get('logged_in'):
    #     return redirect('/admin/login.html')

    orders = local_db.get_unmanaged_orders()
    clusters_nums = list(set(map(lambda x: x['cluster'], orders)))
    return json.dumps({'clusters_nums': clusters_nums}, ensure_ascii=False)


@bp.route('/update_cluster', methods=['POST'])
def upd_cluster():
    local_db.upd_cluster_num(
        request.json['orders_ids'], request.json['new_cluster_num'])
    return 0


@bp.route('/register_cluster_in_yandex', methods=['POST'])
def register_cluster_in_yandex():
    local_db.upd_cluster_seq(request.json['orders_ids'])
    result_code, result_message, yandex_id = create_yandex_order(
        request.json['orders_ids'])

    if result_code == 200:
        # pass
        local_db.register_cluster_in_yandex(
            request.json['orders_ids'], yandex_id)

    resp = {
        'code': result_code,
        'message': result_message
    }
    return json.dumps(resp, ensure_ascii=False)


@bp.route('/create_pdf_for_cluster', methods=['POST'])
def create_pdf_for_cluster():
    local_db.upd_cluster_seq(request.json['orders_ids'])

    try:
        created_file_name = create_invoice_file(request.json['orders_ids'])
        local_db.create_invoice_for_cluster(
            request.json['orders_ids'], created_file_name, str(uuid.uuid1()))
    except Exception as e:
        print(e)
        resp = {
            'code': 500,
            'message': 'что-то пошло нетак при создании накладной'
        }
    else:
        resp = {
            'code': 200,
            'message': 'all ok'
        }

    return json.dumps(resp, ensure_ascii=False)


@bp.route('/invoices.html', methods=['GET'])
def invoices_list():
    orders_and_files = local_db.get_invoice_fileslist()
    invoices = {}
    for x in orders_and_files:
        print('XXXX', x)
        if x['invoice_file_name'] in invoices:
            invoices[x['invoice_file_name']]['orders'].append(
                x['order_id'])
        else:
            invoices[x['invoice_file_name']] = {
                'orders': [x['order_id']],
                'date_managed': x['date_managed']
            }
    invoices_list = []
    for x, y in invoices.items():
        invoices_list.append({
            'invoice_file_name': x,
            'date_managed': y['date_managed'],
            'orders': y['orders']
        })
    print(invoices_list)
    return render_template('/admin/invoices.html', invoices=invoices_list)


@bp.route('get_invoice/<filename>')
def get_invoice_file(filename):
    print('GETTTTTTTT', f'invoices/{filename}')
    with open(f'invoices/{filename}', 'r') as f:
        return f.read()


@bp.route('/manage_managed_orders.html', methods=['GET', 'POST'])
def manage_manage_orders():
    # if not session.get('logged_in'):
    #     return render_template('/admin/login.html')

    if request.method == 'GET':
        orders = local_db.get_managed_orders()
        return render_template('/admin/manage_managed_orders.html', orders=orders)


@bp.route('/drop_managed', methods=['POST'])
def drop_managed():
    def check_invoice_files():
        files = os.listdir(os.getcwd() + os.sep + 'invoices')
        for f in files:
            if local_db.count_orders_for_ivoice_file(f) == 0:
                try:
                    os.remove(os.getcwd() + os.sep + 'invoices' + os.sep + f)
                except:
                    pass

    the_order = local_db.get_order_by_id(request.form['order_id'])

    local_db.drop_formed_order(the_order['del_service_id'])

    check_invoice_files()

    return 'ok'