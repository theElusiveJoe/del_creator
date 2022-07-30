import pandas as pd


def get_order_line_from_ghseets(order_id):
    table = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vQMGGZJHaIPgIpVqpmKQDBhjDWGugEC0p5oUsLNQOPKglSXiTizPigWZMuXGJq-p2XO8MeVPjTGPrIw/pub?gid=1543875454&single=true&output=csv',
                        header=1, usecols=[x for x in range(19)], index_col='Заказ')
    row = table.loc[order_id].iloc[0]

    # row = row.to_dict()
    if row['габариты']:
        gabs = (sorted(list(map(int, row['габариты'].strip().replace('\\', '/').split('/')))))
    else:
        gabs = [0.5, 0.5, 0.5]
    ret = {
        'id': row.name.strip(),
        'weight': float(row['вес'].strip().replace(',', '.')) if 'вес' in row else 0.1,
        'maxlen': gabs[2],
        'midlen': gabs[1],
        'minlen': gabs[0]
    }
    return ret


if __name__ == '__main__':
    get_order_line_from_ghseets('это тест!')