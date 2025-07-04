
import json

import requests


async def get_symbol_inference(symbol, startdate, enddate, api_url):
    payload = {'symbol': symbol, 'startdate': startdate, 'enddate': enddate}
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", api_url, headers=headers, params=payload)
    return json.loads(response.text)


async def get_symbols_correlation(symbol1, symbol2, startdate, enddate, api_url):
    payload = {'symbol1': symbol1, 'symbol2': symbol2, 'startdate': startdate, 'enddate': enddate}
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", api_url, headers=headers, params=payload)
    return json.loads(response.text)


async def get_plots_infos(symbol, startdate, enddate, api_url):
    payload = {'symbol': symbol, 'startdate': startdate, 'enddate': enddate}
    headers = {'Content-Type': 'application/json'}
    response = requests.request('GET', api_url, headers=headers, params=payload)
    return json.loads(response.text)


async def get_ma_plots_info(symbol, startdate, enddate, dayswindow, api_url):
    payload = {'symbol': symbol, 'startdate': startdate, 'enddate': enddate, 'dayswindow': dayswindow}
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", api_url, headers=headers, params=payload)
    return json.loads(response.text)


async def fit_lppl(symbol, startdate, enddate, api_url):
    payload = {'symbol': symbol, 'startdate': startdate, 'enddate': enddate}
    headers = {'Content-Type': 'application/json'}
    response = requests.request("GET", api_url, headers=headers, params=payload)
    return json.loads(response.text)
