from sqlalchemy import create_engine, inspect
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Numeric, Boolean

from apis.geocoder.geocoder import address_to_coords

DBFILEPATH = 'sqlite:///db.db'

# def create_engine_and_meta():
engine = create_engine(DBFILEPATH, echo=True)
meta = MetaData()
# return engine, meta

# def create_table():
    # global orders
    # engine, meta = create_engine_and_meta()
    # if inspect(engine).has_table('orders'):
    #     print('table already exists')
    #     return
    # print('creating')

orders = Table(
    'orders', meta,

    # данные заказа
    Column('order_id', String, primary_key=True),
    Column('paid', Boolean),
    Column('price', String),
    Column('comment', String),

    Column('weight', String),
    Column('positions', Integer),
    Column('size', String),
    Column('del_time_interval', String),

    Column('registered', Boolean),
    Column('cluster', String),

    # данные пользователя
    Column('name', String),
    Column('phone', String),

    # данные адреса
    Column('fullname', String),
    Column('lat', String),
    Column('long', String),
    Column('del_comment', String),
)

meta.create_all(engine)


def add_order(form, gsheets):
    with engine.connect() as conn:
        stmt1 = orders.delete().where(orders.c.order_id == form['order_id'])
        conn.execute(stmt1)

        long, lat = address_to_coords(form['fullname'])
        print('POOOOOOS', gsheets['positions'])
        stmt2 = orders.insert().values(
            order_id=form['order_id'],

            paid=bool(form['paid']),
            price=form['price'],
            comment=form['comment'],

            name=form['name'],
            phone=form['phone'],

            fullname=form['fullname'],
            del_comment=form['del_comment'],
            lat=str(lat),
            long=str(long),

            registered=False,
            cluster='0',
            weight=str(gsheets['weight']),
            positions=int(gsheets['positions']),
            size=gsheets['size'],
            del_time_interval=gsheets['del_time_interval']
        )
        result = conn.execute(stmt2)


def get_orders():
    with engine.connect() as conn:
        stmt = orders.select()
        result = conn.execute(stmt)
        # for row in result:
        #     print(row._mapping)
        return list(map(lambda x: x._asdict(), result))