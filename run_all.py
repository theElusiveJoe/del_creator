from app.app import app as flask_app
from yandex_orders_checker.yandex_orders_checker import Checker

from threading import Thread

flask_app.run(debug=True)
# app_thr = Thread(target=flask_app.run, args={'debug':True})
# checker = Checker('db.db')
# ycheck_thr = Thread(target=checker.run, args={'sleep_time': 3})

# ycheck_thr.run()
# app_thr.run()