from mdutils.mdutils import MdUtils
from db_logic.local_yandex_orders.bd_api_funcs import get_order_by_id
import uuid
import os
import markdown


def create_md(orders_ids, filename):
    mdFile = MdUtils(file_name=filename)
    mdFile.new_header(level=1, title='Список заказов')

    for order_id in orders_ids:
        order = get_order_by_id(order_id)
        mdFile.new_header(level=2, title='заказ ' + order_id)
        # mdFile.new_paragraph('абоба')
        print('FNFFNNFFNNF', order['fullname'])
        mdFile.new_paragraph(
            "**Адрес**: " + order['fullname'] + order['del_comment'])
        mdFile.new_paragraph(
            'координаты: ' + str(order['lat']) + ' : ' + str(order['long']))
        mdFile.new_paragraph('Клиент: ' + order['name'])
        mdFile.new_paragraph('Телефон: ' + order['phone'])
        if order['paid']:
            mdFile.new_paragraph(
                'Заказ оплачен, с клиента не нужно брать деньги')
        else:
            mdFile.new_paragraph(
                f'Заказ не оплачен, с клиента нужно взять {order["price"]} рублей.')
        mdFile.new_paragraph('Позиций в заказе: ' + str(order["positions"]))
        mdFile.new_line()
        mdFile.new_paragraph('Подпись клиента:  \_\_\_\_\_\_\_\_\_\_\_')
        mdFile.new_paragraph()

    mdFile.create_md_file()


def create_invoice_file(orders_ids):
    md_file_name = str(uuid.uuid1())
    create_md(orders_ids, md_file_name)
    html_file_name = '_'.join(orders_ids)
    try:
        os.mkdir('invoices/')
    except:
        pass
    markdown.markdownFromFile(input=md_file_name + '.md', output='invoices/' + html_file_name + '.html')
    os.remove(os.getcwd() + os.sep + md_file_name + '.md')

    return html_file_name + '.html'