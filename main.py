
import re
import os
import logging
import json
from argparse import ArgumentParser

import requests
import telebot


logging.basicConfig(level=logging.INFO)


api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key)


@bot.message_handler(commands=['greet'])
def greet(message):
    logging.info(message)
    bot.reply_to(message, 'Hey, how is it going?')


@bot.message_handler(regexp='[Hh]ello*')
def hello(message):
    logging.info(message)
    bot.send_message(message.chat.id, "Hello!")


@bot.message_handler(regexp='[Bb]ye[!]?')
def sayonara(message):
    logging.info(message)
    bot.send_message(message.chat.id, "Have a nice day!")


def get_tipargparser():
    tipparser = ArgumentParser(description='Tip Calculator')
    tipparser.add_argument('subtotal', type=float)
    tipparser.add_argument('state', type=str)
    tipparser.add_argument('--split', type=int, default=1)
    return tipparser


@bot.message_handler(regexp=r'([tT]ip[s]?)(\s+)([\d]+[\.]?[\d+]?)(\s+)([A-Za-z]+)(\s+\d+)?')
def calculate_tips(message):
    logging.info(message)
    msg_tokens = re.sub('\s+', ' ', message.text).split(' ')[1:]
    if len(msg_tokens) > 2:
        msg_tokens.insert(2, '--split')
    try:
        args = get_tipargparser().parse_args(msg_tokens)
    except Exception:
        bot.send_message(message.chat.id, 'Wrong tip calculator arguments!')
        return

    url = "https://1j79chd1w8.execute-api.us-east-1.amazonaws.com/default/Ingram1623TipCalculator"
    payload = json.dumps({
        "subtotal": args.subtotal,
        "state": args.state,
        "split": args.split
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Amz-Content-Sha256': 'beaead3198f7da1e70d03ab969765e0821b24fc913697e929e726aeaebf0eba3',
        'X-Amz-Date': '20220323T032656Z',
        'Authorization': 'AWS4-HMAC-SHA256 Credential=AKIAV6PASP2CH24VHO3V/20220323/us-east-1/execute-api/aws4_request, SignedHeaders=content-type;host;x-amz-content-sha256;x-amz-date, Signature=d850ee5c12f2c3df740dd211565c0a9709feb7989434eacb6f3a6c50db97f10b'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    result = json.loads(response.text)
    response_text = """
    Subtotal: ${:.2f}
    State: {}
    Tax: ${:.2f}
    Subtotal + Tax: ${:.2f}
    Tips: ${:.2f}
    Total: ${:.2f}
    Each person pays ${:.2f}
    """.format(result['subtotal'], result['state'], result['tax'], result['subtotal']+result['tax'], result['tips'], result['total'], result['onesplit'])
    bot.send_message(message.chat.id, response_text)


bot.polling()
