from app import app
from yandex_orders_checker import Checker

from threading import Thread

app_thr = Thread(target=app.run, args={'debug':True})
checker = Checker('db.db')
ycheck_thr = Thread(target=checker.run, args={'sleep_time': 3})

ycheck_thr.run()
app_thr.run()