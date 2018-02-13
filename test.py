 #!/usr/bin/env python
import time
import numpy
import json
import csv
import shelve
import pygsheets
from Robinhood import Robinhood


def get_symbol_from_instrument_url(rb_client, url, db):
    instrument = {}
    url = str(url)
    if url in db:
        instrument = db[url]
    else:
        db[url] = fetch_json_by_url(rb_client, url)
        instrument = db[url]
    return instrument['symbol']

def fetch_json_by_url(rb_client, url):
    return rb_client.session.get(url).json()

def order_item_info(order, rb_client, db):
    symbol = get_symbol_from_instrument_url(rb_client, order['instrument'], db)
    return {
        'side': order['side'],
        'price': order['average_price'],
        'shares': order['cumulative_quantity'],
        'symbol': symbol,
        'date': order['last_transaction_at'],
        'state': order['state']
    }

def get_all_history_orders(rb_client):
    orders = []
    past_orders = rb.order_history()
    orders.extend(past_orders['results'])
    while past_orders['next']:
        print("{} order fetched".format(len(orders)))
        next_url = past_orders['next']
        past_orders = fetch_json_by_url(rb_client, next_url)
        orders.extend(past_orders['results'])
    print("{} order fetched".format(len(orders)))
    return orders

rb = Robinhood()
rb.login(username="", password="")
past_orders = get_all_history_orders(rb)
instruments_db = shelve.open('instruments2.db')
orders = [order_item_info(order, rb, instruments_db) for order in past_orders]
keys = ['price', 'shares', 'side', 'state', 'date', 'symbol']
with open('orders.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(orders)

try:
    reader = csv.reader(open("orders.csv", "rb"), delimiter=",")
except IOError:
    raise ScriptError('unable to read csv file: csv_file=csv_file')
finally:
    gc = pygsheets.authorize()
    sh = gc.open('my new ssheet')
    wks = sh.sheet1

    cnum = 97
    rnum = 2

    cell_list = []
    for i in range(ord('a'), ord('f')+1):
        cell_list.append(chr(i))

    cell_dict = dict(zip(cell_list, keys))

    x = list(reader)
    values_mat = numpy.array(x)
    wks.update_cells(crange='A1:F61', values=values_mat.tolist())
