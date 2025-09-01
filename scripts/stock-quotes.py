#!/usr/bin/env python3

from pathlib import Path
from polybar import util
from urllib.parse import urlunparse
from urllib.request import urlopen, Request
import argparse
import json
import os
import re
import sys
import urllib.request

def get_stock_quotes(symbols):
    data = {
        'success': False,
        'error':   None,
        'symbols': {},
    }

    url_parts = (
        'https',
        'query1.finance.yahoo.com',
        f'v7/finance/spark?symbols={','.join(symbols)}'
        '',
        '',
        '',
        '',
    )
    url = urlunparse(url_parts)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }

    req = Request(url, headers=headers)

    with urlopen(req) as response:
        status = response.status
        if status == 200:
            body = response.read().decode('utf-8')
            
            try:
                json_data = json.loads(body)
                
            except Exception as e:
                data['error'] = e
                return data
        else:
            data['error'] = 'non-200 return code received'
            return data

    if 'spark' in json_data:
        if 'result' in json_data['spark']:
            if len(json_data['spark']['result']) > 0:
                data['success'] = True
                for block in json_data['spark']['result']:
                    symbol = block['symbol']
                    if not symbol in data['symbols']:
                        meta = block['response'][0]['meta']
                        data['symbols'][symbol] = {}
                        data['symbols'][symbol]['price'] = meta['regularMarketPrice']
                        data['symbols'][symbol]['last'] = meta['previousClose']
                        data['symbols'][symbol]['currency'] = meta['currency']
                        data['symbols'][symbol]['symbol'] = meta['symbol']
            else:
                data['error'] = 'no stock data found'
        else:
            data['error'] = 'incomplete stock data'
    else:
        data['error'] = 'incomplete stock data'

    return data

def main():
    arrow_down = util.surrogatepass('\uea9d') # cod_arrow_small_down
    arrow_up = util.surrogatepass('\ueaa0') # cod_arrow_small_up
    graph_icon = util.surrogatepass('\uebe2') # cod_graph_line
    max_symbols = 5

    parser = argparse.ArgumentParser(description="Look stock quotes up from Yahoo! Finance")
    parser.add_argument("-s", "--symbol", action='append', help="The symbol to lookup; can be used multiple times", required=True)
    args = parser.parse_args()
    
    quotes = get_stock_quotes(args.symbol)

    output = []
    for symbol, quote in quotes['symbols'].items():
        if quote['price'] is not None and quote['last'] is not None:
            price = quote['price']
            last = quote['last']
            if price > last:
                arrow = arrow_up
                change_amount = f'{util.pad_float((price - last))}'
                pct_change = f'{util.pad_float((price - last) / last * 100)}'
            else:
                arrow = arrow_down
                change_amount = f'{util.pad_float((float(last - price)))}'
                pct_change = f'{util.pad_float((last - price) / last * 100)}'
            output.append(f'{util.colorize(graph_icon)} {symbol} ${price} {arrow}${change_amount} ({pct_change}%)')

    print(' | '.join(output))

if __name__ == "__main__":
    main()