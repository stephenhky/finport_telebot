
import json

import requests


async def get_symbol_inference(symbol, startdate, enddate, api_url):
    payload = json.dumps({
        'symbol': symbol,
        'startdate': startdate,
        'enddate': enddate
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", api_url, headers=headers, data=payload)
    return json.loads(response.text)


async def get_symbols_correlation(symbol1, symbol2, startdate, enddate, api_url):
    payload = {
        'symbol1': symbol1,
        'symbol2': symbol2,
        'startdate': startdate,
        'enddate': enddate
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", api_url, headers=headers, data=payload)
    return json.loads(response.text)
