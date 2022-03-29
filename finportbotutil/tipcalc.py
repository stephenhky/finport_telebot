
import json
from argparse import ArgumentParser

import requests


def get_tipargparser():
    tipparser = ArgumentParser(description='Tip Calculator')
    tipparser.add_argument('subtotal', type=float)
    tipparser.add_argument('state', type=str)
    tipparser.add_argument('--split', type=int, default=1)
    return tipparser


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


