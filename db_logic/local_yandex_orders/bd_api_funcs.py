from sqlalchemy import create_engine, inspect
from sqlalchemy import Table, Column, Integer, String, MetaData, Date, Numeric, Boolean
from sqlalchemy import insert, update, delete

DBFILEPATH = 'sqlite:///{db.db}'

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
    Column('price', Numeric),
    Column('comment', String),

    # данные пользователя
    Column('name', String),
    Column('phone', String),

    # данные адреса
    Column('fullname', String),
    Column('del_comment', String),
)

meta.create_all(engine)


def add_order(form):
    # create_table()

    # engine, _ = create_engine_and_meta()
    with engine.connect() as conn:
        stmt1 = orders.delete().where(orders.c.order_id == form['order_id'])
        conn.execute(stmt1)
        stmt2 = orders.insert().values(
            order_id=form['order_id'],
            paid=bool(form['paid']),
            price=float(form['price']),
            comment=form['comment'],
            name=form['name'],
            phone=form['phone'],
            fullname=form['fullname'],
            del_comment=form['del_comment'],
        )
        result = conn.execute(stmt2)

