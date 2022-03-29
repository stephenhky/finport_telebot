
import json
from argparse import ArgumentParser

import requests


def get_tipargparser():
    tipparser = ArgumentParser(description='Tip Calculator')
    tipparser.add_argument('subtotal', type=float)
    tipparser.add_argument('state', type=str)
    tipparser.add_argument('--split', type=int, default=1)
    return tipparser


def calculate_tips(subtotal, state, nbsplits):
    url = "https://1j79chd1w8.execute-api.us-east-1.amazonaws.com/default/Ingram1623TipCalculator"
    payload = json.dumps({
        "subtotal": subtotal,
        "state": state,
        "split": nbsplits
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Amz-Content-Sha256': 'beaead3198f7da1e70d03ab969765e0821b24fc913697e929e726aeaebf0eba3',
        'X-Amz-Date': '20220323T032656Z',
        'Authorization': 'AWS4-HMAC-SHA256 Credential=AKIAV6PASP2CH24VHO3V/20220323/us-east-1/execute-api/aws4_request, SignedHeaders=content-type;host;x-amz-content-sha256;x-amz-date, Signature=d850ee5c12f2c3df740dd211565c0a9709feb7989434eacb6f3a6c50db97f10b'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    result = json.loads(response.text)
    return result


