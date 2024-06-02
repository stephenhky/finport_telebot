
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
    payload = json.dumps({
        'symbol1': symbol1,
        'symbol2': symbol2,
        'startdate': startdate,
        'enddate': enddate
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", api_url, headers=headers, data=payload)
    return json.loads(response.text)


async def get_plots_infos(symbol, startdate, enddate, api_url):
    done = False
    while not done:
        payload = json.dumps({
            'startdate': startdate,
            'enddate': enddate,
            'components': {
                'name': 'DynamicPortfolio',
                'current_date': enddate,
                'timeseries': [
                    {
                        'date': startdate,
                        'portfolio': {symbol: 1}
                    }
                ]
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request('GET', api_url, headers=headers, data=payload)

        response_dict = json.loads(response.text)
        if 'plot' in response_dict:
            done = True
    return response_dict


async def get_ma_plots_info(symbol, startdate, enddate, dayswindow, api_url, title=None):
    payload = json.dumps({
        'symbol': symbol,
        'startdate': startdate,
        'enddate': enddate,
        'dayswindow': dayswindow,
        'title': symbol if title is None else title
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", api_url, headers=headers, data=payload)
    return json.loads(response.text)


async def fit_lppl(symbol, startdate, enddate, api_url):
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
