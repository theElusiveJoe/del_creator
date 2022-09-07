import os
import sys
import sqlite3
import time
import logging
import json
from geopy.distance import geodesic

from apis.yandex_go.yandex_go import yandex_get_smth, yandex_performer_position
from apis.yandex_go.yandex_go import yandex_create, yandex_approve, yandex_repeat

from bot import TG_Bot

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class Checker:
    def __init__(self, db_path='db.db'):
        self.tg_bot = TG_Bot(db_path=db_path)
        self.tg_bot.start()
        self.db_path = db_path

        with open(os.path.join(sys.path[0], 'constants/yandex_go_constants.json'), 'r') as yc:
            yandex_constants = json.load(yc)
        self.coords = (yandex_constants['template']['route_points'][0]
                       ['address']['coordinates'][1],
                       yandex_constants['template']['route_points'][0]
                       ['address']['coordinates'][0])

        handler = logging.StreamHandler(stream=sys.stdout)
        log = logging.getLogger(__name__)
        log.addHandler(handler)
        self.log = log

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

    def delete_from_db(self, claim_id):
        self.check_db_file_and_table()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""DELETE FROM yandex_orders
            WHERE id = "{claim_id}"
            ;"""
            )
            conn.commit()

    def set_status_in_db(self, claim_id, new_status):
        with sqlite3.connect(self.db_path) as conn:
                            cur = conn.cursor()
                            cur.execute(
                                f"""UPDATE yandex_orders
                            SET status = "{new_status}"
                            WHERE id = {claim_id}
                            ;""")
                            conn.commit()

    def check_all_orders(self):
        self.check_db_file_and_table()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""SELECT id, status, version FROM yandex_orders
            ORDER BY status;
            """
            )
            orders = cur.fetchall()

        for order in orders:
            claim_id, status_in_db, version_in_db = order
            status = yandex_get_smth(claim_id, 'status')
            self.log.info(
                f'CHECKER check_all "{claim_id}":\n    status: {status}')

            # Бот пишет в чат при следующих событиях:
            # * old_bd_status -> подтвердили -> approvement_allerted
            # * old_bd_status -> курьер на подходе -> vicinity_allerted
            # * vicinity_allerted -> курьер прибыл -> arrivival_allerted
            # * заказ окончен или отменен ->удалить из бд
            # * ошибка с заказом -> удалить из бд
            try:
                if status == 'ready_for_approval':
                    # print('------ аппрувнуть бы')
                    yandex_approve(claim_id, version_in_db)
                    self.tg_bot.broadcast(
                        f"""🆕🆕🆕 Поступил и был подтвержден новый заказ 🆕🆕🆕\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}""")
                    self.set_status_in_db(claim_id, 'approvement_allerted')

                elif status in ['new', 'estimating', 'accepted',
                                'performer_lookup', 'performer_draft']:
                    # print('------ всё хорошо, ничего не делаем')
                    pass

                elif status in ['failed', 'performer_not_found', \
                    'cancelled_by_taxi', 'estimating_failed']:
                    # print('------ беда с заказом')
                    self.tg_bot.broadcast(
                        f"""❗️❗️❗️ ОШИБКА С ЗАКАЗОМ ❗️❗️❗️\n
                        статус: {status}\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}"""
                    )
                    self.delete_from_db(claim_id)

                elif status in ['cancelled', 'cancelled_with_payment', \
                    'cancelled_with_items_on_hands']:
                    # print('------ удаляем')
                    self.delete_from_db(claim_id)
                    self.tg_bot.broadcast(
                        f"""❔❔❔ Заказ отменен ❔❔❔\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}"""
                    )

                elif status == 'delivered_finish':
                    self.delete_from_db(claim_id)
                    self.tg_bot.broadcast(
                        f"""✅✅✅ Доставка успешно завершена ✅✅✅\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}"""
                    )

                elif status == 'performer_found' and not (status_in_db == 'vicinity_allerted'):
                    performer_coords = yandex_performer_position(claim_id)

                    if geodesic(performer_coords, self.coords).m < 500:
                        self.tg_bot.broadcast(
                            f"""🚶‍♂️🚶‍♂️🚶‍♂️Курьер на подходе🚶‍♂️🚶‍♂️🚶‍♂️\n
                            id: {yandex_get_smth(claim_id, 'id')}\n
                            claim_id: {claim_id}"""
                        )
                        self.set_status_in_db(claim_id, 'vicinity_allerted')

                elif status == 'pickup_arrived' and not (status_in_db == 'arrival_allerted'):                    
                    self.tg_bot.broadcast(
                        f"""📦📦📦Курьер прибыл📦📦📦\n
                        id: {yandex_get_smth(claim_id, 'id')}\n
                        claim_id: {claim_id}"""
                    )
                    self.set_status_in_db(claim_id, 'arrival_allerted')

            except Exception as e:
                logging.exception(e)

    def run(self, sleep_time=30):
        while True:
            # print(time.asctime())
            self.check_all_orders()
            time.sleep(sleep_time)


if __name__ == '__main__':
    print('checker started')
    Checker(db_path='db.db').run(sleep_time=3)
