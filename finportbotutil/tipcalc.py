
import json

import requests


def calculate_tips(
        subtotal,
        state,
        nbsplits,
        api_url
):
    payload = json.dumps({
        "subtotal": subtotal,
        "state": state,
        "split": nbsplits
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", api_url, headers=headers, data=payload)
    result = json.loads(response.text)
    return result


