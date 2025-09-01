#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, util
from urllib.parse import urlunparse
from urllib.request import urlopen, Request
import argparse
import json
import sys
import urllib.request

def get_stock_quotes(symbol):
    data = {
        'success':     False,
        'error':       None,
        'symbol_data': {},
    }

    url_parts = (
        'https',
        'query1.finance.yahoo.com',
        f'v7/finance/spark?symbols={symbol}'
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
                    meta = block['response'][0]['meta']
                    data['symbol_data']['price'] = meta['regularMarketPrice']
                    data['symbol_data']['last'] = meta['previousClose']
                    data['symbol_data']['currency'] = meta['currency']
                    data['symbol_data']['symbol'] = meta['symbol']
            else:
                data['error'] = 'no stock data found'
        else:
            data['error'] = 'incomplete stock data'
    else:
        data['error'] = 'incomplete stock data'

    return data

def main():
    parser = argparse.ArgumentParser(description="Look stock quotes up from Yahoo! Finance")
    parser.add_argument("-s", "--symbol", help="The symbol to lookup", required=True)
    args = parser.parse_args()
    
    quote = get_stock_quotes(args.symbol)

    if quote['symbol_data']['price'] is not None and quote['symbol_data']['last'] is not None:
        price = quote['symbol_data']['price']
        last = quote['symbol_data']['last']

        if price > last:
            arrow = glyphs.cod_arrow_small_up
            change_amount = f'{util.pad_float((price - last))}'
            pct_change = f'{util.pad_float((price - last) / last * 100)}'
        else:
            arrow = glyphs.cod_arrow_small_down
            change_amount = f'{util.pad_float((float(last - price)))}'
            pct_change = f'{util.pad_float((last - price) / last * 100)}'
        print(f'{util.color_title(glyphs.cod_graph_line)} {args.symbol} ${price} {arrow}${change_amount} ({pct_change}%)')
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()