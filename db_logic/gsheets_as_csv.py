import pandas as pd
import logging
import sys

handler = logging.StreamHandler(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)


def get_order_line_from_ghseets(order_id):
    log.info(f'GSHEETS get_line "{order_id}"')
    try:
        table = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vQMGGZJHaIPgIpVqpmKQDBhjDWGugEC0p5oUsLNQOPKglSXiTizPigWZMuXGJq-p2XO8MeVPjTGPrIw/pub?gid=1543875454&single=true&output=csv',
                            header=1, usecols=[x for x in range(19)], index_col='Заказ')
        row = table.loc[order_id]
        if row['габариты']:
            gabs = (
                sorted(list(map(int, row['габариты'].strip().replace('\\', '/').split('/')))))
        else:
            gabs = [0.5, 0.5, 0.5]
        ret = {
            'id': row.name.strip(),
            'weight': float(row['вес'].strip().replace(',', '.')) if 'вес' in row else 0.1,
            'maxlen': gabs[2],
            'midlen': gabs[1],
            'minlen': gabs[0]
        }
        log.info(f'GSHEETS get_line "{order_id}" - correct')
        return ret
    except:
        log.warning(f'GSHEETS get_line "{order_id}" - error')
        raise Exception('Проблемы с гугл таблицей')


if __name__ == '__main__':
    get_order_line_from_ghseets('test1')
