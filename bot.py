import telegram.ext as tg
import os
import sys
import json
import time
import sqlite3
import logging


class TG_Bot():
    def __init__(self, db_path='db.db'):
        def start_hf(update, context):
            # print('NEW CHAT, ID:', update.effective_chat.id)
            self.add_chat_id(update.effective_chat.id)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Теперь сюда будет поступать рассылка по заказам")

        def stop_hf(update, context):
            # print('DELETE CHAT, ID:', update.effective_chat.id)
            self.delete_chat_id(update.effective_chat.id)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Рассылка по заказам приостановлена")

        with open(os.path.join(sys.path[0], 'tokens.json'), 'r') as tokens:
            tokens = json.load(tokens)
            self.TOKEN = tokens['tg_bot_token']

        self.db_path = db_path

        self.db_file_path = os.path.join(sys.path[0], self.db_path)

        self.updater = tg.Updater(token=self.TOKEN)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(tg.CommandHandler('start', start_hf))
        self.dispatcher.add_handler(tg.CommandHandler('stop', stop_hf))

    def start(self):
        self.updater.start_polling()

    def broadcast(self, message_text):
        for chat_id in self.get_chat_ids():
            self.dispatcher.bot.send_message(chat_id, message_text)

    def check_db_file_and_table(self):
        try:
            with open(self.db_file_path, 'x') as fp:
                pass
        except:
            pass

        with sqlite3.connect(self.db_file_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""CREATE TABLE IF NOT EXISTS active_chats(
                chat_id          INTEGER PRIMARY KEY
                );"""
            )
            conn.commit()

    def delete_chat_id(self, id_to_del):
        self.check_db_file_and_table()
        with sqlite3.connect(self.db_file_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""DELETE FROM active_chats
            WHERE chat_id = {id_to_del};
            """
            )
            conn.commit()

    def add_chat_id(self, new_id):
        self.check_db_file_and_table()
        # print('NEWID:', new_id)
        with sqlite3.connect(self.db_file_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""INSERT OR IGNORE INTO active_chats (chat_id)
            VALUES ({new_id});
            """
            )
            conn.commit()

    def get_chat_ids(self):
        self.check_db_file_and_table()
        with sqlite3.connect(self.db_file_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""SELECT chat_id FROM active_chats;
            """
            )
            return map(lambda x: x[0], cur.fetchall())


if __name__ == '__main__':
    bot = TG_Bot()

    while True:
        bot.start()
        bot.broadcast(f'time {time.time()}')
        time.sleep(3)
