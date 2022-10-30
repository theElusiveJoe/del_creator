from sqlalchemy import create_engine, inspect, update, select, desc, delete
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, Numeric, Boolean, Float

from apis.geocoder.geocoder import address_to_coords

import phonenumbers
import datetime

DBFILEPATH = 'sqlite:///db.db'

engine = create_engine(DBFILEPATH, echo=True)
meta = MetaData()


orders = Table(
    'orders', meta,

    # данные заказа
    Column('order_id', String, primary_key=True),
    Column('paid', Boolean),
    Column('price', String),
    Column('comment', String),

    Column('weight', Float),
    Column('positions', Integer),
    Column('size_x', Integer),
    Column('size_y', Integer),
    Column('size_z', Integer),
    Column('del_time_interval', String),

    Column('del_service', String),  # yandex, carrier
    Column('del_service_id', String),  # для заказов из яндекса
    Column('invoice_file_name', String),
    Column('cluster', String),
    Column('seq_num', Integer),
    Column('date_managed', DateTime),

    # данные пользователя
    Column('name', String),
    Column('phone', String),

    # данные адреса
    Column('fullname', String),
    Column('lat', Float),
    Column('long', Float),
    Column('del_comment', String),
)

meta.create_all(engine)


def drop_old_orders():
    with engine.connect() as conn:
        orders_list = conn.execute(select(orders.c.order_id, orders.c.date_managed).where(orders.c.date_managed != None)).fetchall()
        orders_list = list(map(lambda x: x._asdict(), orders_list))
        for order in orders_list:
            print(datetime.datetime.now(), order['date_managed'])
            if (datetime.datetime.now() - order['date_managed']).days > 30:
                stmt = (
                    delete(orders).
                    where(orders.c.order_id == order['order_id'])
                )
                conn.execute(stmt)


def add_order(form, gsheets):
    with engine.connect() as conn:

        # ищем косяки в данных
        try:
            long, lat = address_to_coords(form['fullname'])
        except:
            return f'Проблема с адресом - не могу найти его кооординаты: {form["fullaname"] if form["fullaname"] else "адрес пуст"}'

        try:
            size_x, size_y, size_z = list(
                map(float, gsheets['size'].replace('\\', '/').strip().split('/')))
        except:
            return f'Проблемы с габаритами в гугл таблице: {gsheets["size"] if gsheets["size"] else "их нет"}'

        try:
            form['phone'] = phonenumbers.format_number(
                phonenumbers.parse(form['phone'], 'RU'), phonenumbers.PhoneNumberFormat().E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            return f'Ошибка парсинга телефона: {form["phone"] if form["phone"] else "его нет"}'

        # ищем новый заказ в базе
        stmt1 = select(orders).where(orders.c.order_id == form['order_id'])
        result = conn.execute(stmt1).fetchone()

        if not result:
            # если заказа нет, то вставляем
            stmt2 = orders.insert().values(
                order_id=form['order_id'],

                paid=bool(int(form['paid'])),
                price=form['price'],
                comment=form['comment'],

                name=form['name'],
                phone=form['phone'],

                fullname=form['fullname'],
                del_comment=form['del_comment'],
                lat=lat,
                long=long,

                cluster='0',

                weight=float(str(gsheets['weight']).replace(',', '.')),
                positions=int(gsheets['positions']),
                size_x=size_x/100,
                size_y=size_y/100,
                size_z=size_z/100,
                del_time_interval=gsheets['del_time_interval']
            )
        else:
            # иначе, обновляем данные по этому заказу
            stmt2 = update(orders).where(orders.c.order_id == form['order_id']).values(
                paid=bool(int(form['paid'])),
                price=form['price'],
                comment=form['comment'],

                name=form['name'],
                phone=form['phone'],

                fullname=form['fullname'],
                del_comment=form['del_comment'],
                lat=lat,
                long=long,

                cluster='0',

                weight=float(str(gsheets['weight']).replace(',', '.')),
                positions=int(gsheets['positions']),
                size_x=size_x/100,
                size_y=size_y/100,
                size_z=size_z/100,
                del_time_interval=gsheets['del_time_interval']
            )
        stmt2 = stmt2

        result = conn.execute(stmt2)


def get_unmanaged_orders():
    with engine.connect() as conn:
        stmt = (
            select(orders).
            where(orders.c.del_service == None)
        )
        result = conn.execute(stmt)

        return list(map(lambda x: x._asdict(), result))


def get_managed_orders():
    with engine.connect() as conn:
        stmt = (
            select(orders).
            where(orders.c.del_service != None)
        )
        result = conn.execute(stmt)

        result = list(map(lambda x: x._asdict(), result))
        result.sort(key=lambda x: x['date_managed'], reverse=True)
        for i, _ in enumerate(result):
            result[i]['date_managed'] = result[i]['date_managed'].strftime(
                '%H:%M %d/%m/%Y')
        return result


def get_orders_by_cluster(cl_num):
    with engine.connect() as conn:
        stmt = (
            select(orders).
            where(orders.c.cluster == cl_num)
        )
        result = conn.execute(stmt)
        return list(map(lambda x: x._asdict(), result))


def get_order_by_id(order_id):
    with engine.connect() as conn:
        stmt = orders.select().where(orders.c.order_id == order_id)
        result = conn.execute(stmt).fetchone()
        print(result)
        if result:
            return result._asdict()
        return None


def get_orders_by_del_service_id(del_service_id):
    with engine.connect() as conn:
        stmt = select(orders.c.order_id).where(
            orders.c.del_service_id == del_service_id)
        result = conn.execute(stmt)
        return list(map(lambda x: x._asdict()['order_id'], result))


def get_invoice_fileslist():
    with engine.connect() as conn:
        stmt = (
            select(orders.c.invoice_file_name, orders.c.date_managed, orders.c.order_id).
            where(orders.c.invoice_file_name != None).
            order_by(desc(orders.c.date_managed))
        )
        result = conn.execute(stmt)

        result = list(map(lambda x: x._asdict(), result))
        # result.sort(key=lambda x: x['date_managed'])
        for i, _ in enumerate(result):
            result[i]['date_managed'] = result[i]['date_managed'].strftime(
                '%H:%M %d/%m/%Y')
        return result


def upd_cluster_num(orders_ids, new_cluster_num):
    with engine.connect() as conn:
        for order_id in orders_ids:
            stmt = (
                update(orders).
                where(orders.c.order_id == order_id).
                values(cluster=new_cluster_num)
            )
            conn.execute(stmt)


def upd_cluster_seq(orders_ids):
    with engine.connect() as conn:
        for i, order_id in enumerate(orders_ids):
            stmt = (
                update(orders).
                where(orders.c.order_id == order_id).
                values(seq_num=i+2)
            )
            conn.execute(stmt)


def register_cluster_in_yandex(orders_ids, yandex_id):
    with engine.connect() as conn:
        for i, order_id in enumerate(orders_ids):
            stmt = (
                update(orders).
                where(orders.c.order_id == order_id).
                values(cluster=None, del_service='yandex',
                       del_service_id=yandex_id, date_managed=datetime.datetime.now())
            )
            conn.execute(stmt)


def create_invoice_for_cluster(orders_ids, invoice_file_name, cluster_uuid):
    with engine.connect() as conn:
        for i, order_id in enumerate(orders_ids):
            stmt = (
                update(orders).
                where(orders.c.order_id == order_id).
                values(cluster=None, del_service='carrier',
                       invoice_file_name=invoice_file_name, date_managed=datetime.datetime.now(), del_service_id=cluster_uuid)
            )
            conn.execute(stmt)


def drop_formed_order(order_uuid):
    with engine.connect() as conn:
        stmt = (
            update(orders).
            where(orders.c.del_service_id == order_uuid).
            values(cluster=0, del_service=None, date_managed=None,
                   del_service_id=None, invoice_file_name=None)
        )
        conn.execute(stmt)


def pop_from_formed_order(order_id):
    drop_old_orders()
    with engine.connect() as conn:
        stmt = (
            update(orders).
            where(orders.c.order_id == order_id).
            values(cluster=0, del_service=None, date_managed=None,
                   del_service_id=None, invoice_file_name=None)
        )
        conn.execute(stmt)


def count_orders_for_ivoice_file(filename):
    with engine.connect() as conn:
        stmt = (
            select(orders).
            where(orders.c.invoice_file_name == filename)
        )
        result = len(conn.execute(stmt).fetchall())
    return result
