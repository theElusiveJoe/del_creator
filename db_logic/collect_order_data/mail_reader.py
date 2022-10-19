import imaplib
import email

from bs4 import BeautifulSoup

import pandas as pd

import json
import re
import copy
import logging

with open('tokens/tokens.json', 'r') as f:
    tokens = json.load(f)
    username = tokens['ymail']['username']
    password = tokens['ymail']['password']


def price_to_num(st):
    return re.search('[.,\d]+', st)[0]


ftempl = open('db_logic/collect_order_data/zippack_patterm.json', 'r')
the_json_main = json.load(ftempl)


def get_order_from_mail(order_raw_num):
    # настраиваем соединение
    mail = imaplib.IMAP4_SSL('imap.yandex.ru')
    mail.login(username, password)
    mail.select('INBOX', readonly=True)

    # получаем письмо
    result, data = mail.search(
        None, f'(SUBJECT "{order_raw_num} - spbkonvert.com")')

    ids = data[0]  # Получаем строку номеров писем
    id_list = ids.split()  # Разделяем ID писем
    try:
        latest_email_id = id_list[0]  # Берем первое упоминание
    except:
        # logging.exception('')
        logging.error('##########ПИСЬМО НЕ НАйДЕНО##########')
        return
        
    # Получаем тело письма (RFC822) для данного ID
    try:
        result, data = mail.fetch(latest_email_id, "(RFC822)")
    except:
        logging.error('##########НЕ УДАЛОСЬ ПОЛУЧИТЬ ТЕЛО ПИСЬМА##########')
    msg = email.message_from_bytes(data[0][1])

    try:
        # парсим json шаблон
        # ftempl = open('compose_data/zippack_patterm.json', 'r')
        the_json = copy.copy(the_json_main)
        obj = the_json['obj']

        # выцепляем html часть
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                pl = part.get_payload(decode='base64')
                soup = BeautifulSoup(pl, 'html.parser')
                break
        # находим таблички с товарами
        itemtables = soup.find_all('table', attrs={'cellspacing': '1'})
        items = []
        price = 0
        keys = [('Арт.', 'ArtNo'),
                ('Название', 'Name'),
                ('Цена', 'Price'),
                ('Количество', 'Amount')]
        for itemtable in itemtables:
            tabl = pd.read_html(str(itemtable))[0]
            for i in range(len(tabl)):
                item = tabl.iloc[i]
                m = {}
                for nameru, name in keys:
                    m[name] = item[nameru] if nameru in item.keys() else None
                m['Price'] = float(price_to_num(m['Price']))
                m['Amount'] = int(m['Amount'])
                m['ArtNo'] = str(m['ArtNo'])
                if m['Name'] is None:
                    m['Name'] = item['Описание'] if 'Описание' in item.keys(
                    ) else "название не нашлось. сообщите в тех поддержку"
                items.append(m)
        obj['Items'] = items

        # находим табличку с итоговой ценой
        pricetable = soup.find_all('table', attrs={'cellspacing': '2'})
        # sum = pd.read_html(str(pricetable))[1].iloc[0]['Итого c учетом доставки и скидок']
        # pricetable
        # pd.read_html(str(pricetable).replace(',', ''))
        obj['Sum'] = float(price_to_num(
            pricetable[0].find_all('strong')[-1].text))

        # находим скидку
        disc = soup.find_all('strong', attrs={'style': 'color: #d00'})
        if disc != []:
            potent = re.search('\d+.\d+%', disc[0].text)
            if potent is not None:
                obj['OrderDiscount'] = float(potent.group(0)[:-1])

        # табличка с информацией о заказе
        order_info_table = soup.find_all('table', attrs={'cellspacing': '0'})
        order_info = pd.read_html(str(order_info_table))[1].set_index(0)
        order_info = order_info.transpose().iloc[0]
        # print(order_info)

        # информация о клиенте
        tags = [
            ('Название организации или Ф.И.О.:', 'FirstName'),
            ('Адрес электронной почты:', 'Email'),
            ('Код города и номер телефонa:', 'Phone'),
            ('Страна доставки:', 'Country'),
            ('Город доставки:', 'City'),
            ('Город доставки:', 'Region'),
            ('Комментарий к заказу:', 'CustomerComment')
        ]
        for x, y in tags:
            if x in order_info.keys():
                obj['Customer'][y] = order_info.loc[x]

        # информация о доставке
        shipping_type = order_info.loc['Способ получения:'] if 'Способ получения:' in order_info.keys() else ''
        print(shipping_type, type(shipping_type))

        if pd.isna(shipping_type) \
                or shipping_type == 'Самовывоз. 1-2 дня' \
                or shipping_type.startswith('DPD') and 'курьером до двери' not in shipping_type \
                or shipping_type == 'Самовывоз':
            obj['Customer']['CustomField1'] = order_info.loc['Выбранный пункт самовывоза:']
        elif shipping_type.startswith('Курьер - ДО АДРЕСА.') \
                or shipping_type.startswith('СДЭК') \
                or 'курьером до двери' in shipping_type:
            obj['Customer']['CustomField1'] = order_info.loc['Адрес доставки, Ф.И.О. и телефоны контактного лица:']
        else:
            obj['Customer']['CustomField1'] = ""

        obj['ShippingCost'] = float(price_to_num(
            order_info.loc['Стоимость доставки:']))

        # выцепляем текстовую часть
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                text = part.get_payload(decode='base64').decode('utf8')
                # print(text)
                break

        # разбиваем на строчки
        strs = text.replace('\r\n\r\n', '\r\n').split('\r\n')
        num = re.search('№\d*\s', strs[0])
        obj['Number'] = strs[0][num.start()+1:num.end()-1]

        obj['PaymentName'] = strs[strs.index('Способ оплаты:')+1]
    except:
        logging.exception('Возникли проблемы при парсинге письма')
        # logging.error('Возникли проблемы при парсинге письма')
    the_json['obj'] = obj

    return the_json

if __name__ == '__main__':
    f = open('smth.json', 'w')
    f.write(get_order_from_mail(76451))
