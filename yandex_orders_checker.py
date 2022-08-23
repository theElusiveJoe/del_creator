import os
import sys
import sqlite3
import time
import logging
from geopy.distance import geodesic

from apis.yandex_go.yandex_go import yandex_get_smth, yandex_performer_position
from apis.yandex_go.yandex_go import yandex_create, yandex_approve, yandex_repeat

from bot import TG_Bot


class Checker:
    def __init__(self, db_path='db.db'):
        self.tg_bot = TG_Bot(db_path=db_path)
        self.tg_bot.start()
        self.db_path = db_path

        with open(os.path.join(sys.path[0], 'constants/yandex_go_constants.json'), 'r') as yc:
            yandex_constants = json.load(yc)
        self.coords = (yandex_constants['template']['route_points'][0]['address']['coordinates'][1], 
                    yandex_constants['template']['route_points'][0]['address']['coordinates'][0])

    def check_db_file_and_table(self):
        try:
            with open(self.db_path, 'x') as fp:
                pass
        except:
            pass

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
            f"""CREATE TABLE IF NOT EXISTS  yandex_orders(
            id          TEXT PRIMARY KEY,
            status      Text
            );"""
            )
            conn.commit()

    def delete_from_table(self, claim_id):
        self.check_db_file_and_table()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
            f"""DELETE FROM yandex_orders
            WHERE id = "{claim_id}"
            ;"""
            )
            conn.commit()


    def check_all_orders(self):
        self.check_db_file_and_table()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""SELECT id, status FROM yandex_orders
            ORDER BY status;
            """
            )
            orders = cur.fetchall()

        for order in orders:
            claim_id = order[0]
            status = yandex_get_smth(claim_id, 'status')
            print('ORDER:', claim_id, status)
            try:
                if status == 'ready_for_approval':
                    # yandex_approve(claim_id)
                    print('------ аппрувнуть бы')
                elif status in ['new', 'estimating', 'accepted',
                                'performer_lookup', 'performer_draft']:
                    print('------ всё хорошо, ничего не делаем')
                elif status in ['failed', 'performer_not_found', 'cancelled_by_taxi', 'estimating_failed']:
                    print('------ беда с заказом')
                    self.tg_bot.broadcast(
                        f"""❗️❗️❗️ОШИБКА ПРИ СОЗДАНИИ❗️❗️❗️\n
                        статус: {status}\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}""")
                elif status in ['cancelled', 'cancelled_with_payment', 'cancelled_with_items_on_hands', 'delivered_finish']:
                    self.delete_from_table(claim_id)
                    print('------ удаляем')
                elif status == 'performer_found':
                    if order[1] == 'arriving_allerted':
                        continue

                    performer_coords = yandex_performer_position(claim_id)
                    if geodesic(performer_coords, self.coords).m < 1500:
                        self.tg_bot.broadcast(
                        f"""Курьер на подходе O_O\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}""")
                        with sqlite3.connect(self.db_path) as conn:
                            cur = conn.cursor()
                            cur.execute(
                            f"""UPDATE yandex_orders
                            SET status = {'arriving_allerted'}
                            WHERE id = {claim_id}
                            ;""")
                            conn.commit()
                elif status == 'pickup_arrived':
                    self.tg_bot.broadcast(
                    f"""Курьер прибыл!!!!!\n
                    id: {yandex_get_smth(claim_id, 'id')}\n
                    claim_id: {claim_id}""")
                    with sqlite3.connect(self.db_path) as conn:
                        cur = conn.cursor()
                        cur.execute(
                        f"""UPDATE yandex_orders
                        SET status = {'pickup_arrived'}
                        WHERE id = {claim_id}
                        ;""")
                        conn.commit()    
            except Exception as e:
                logging.exception(e)

    def run(self, sleep_time=30):
        while True:
            print(time.asctime())
            self.check_all_orders()
            time.sleep(sleep_time)

if __name__ == '__main__':
    Checker(db_path='db.db').run(sleep_time=3)