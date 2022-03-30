
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
    result = json.loads(response.text)
    return result
