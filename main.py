
import re
import os
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import asyncio

import numpy as np
import telebot

from finportbotutil.tipcalc import get_tipargparser, calculate_tips
from finportbotutil.syminfo import get_symbol_inference, get_symbols_correlation

logging.basicConfig(level=logging.INFO)


# Telebot API Key
api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key)

# Tip Calculator API
tipcalc_api_url = os.getenv('TIPCALCURL')

# Stock inference API
stockinfo_api_url = os.getenv('FININFO')

# Stock correlation API
stockcorr_api_url = os.getenv('STOCKCORR')


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


@bot.message_handler(regexp=r'([tT]ip[s]?)(\s+)([\d]+[\.]?[\d+]?)(\s+)([A-Za-z]+)(\s+\d+)?')
def handling_tips_message(message):
    logging.info(message)
    msg_tokens = re.sub('\s+', ' ', message.text).split(' ')[1:]
    if len(msg_tokens) > 2:
        msg_tokens.insert(2, '--split')
    try:
        args = get_tipargparser().parse_args(msg_tokens)
    except Exception:
        bot.send_message(message.chat.id, 'Wrong tip calculator arguments!')
        return

    result = calculate_tips(args.subtotal, args.state, args.split, tipcalc_api_url)

    response_text = open(os.path.join('messagetemplates', 'tipcalc.txt')).read().format(
        subtotal=result['subtotal'],
        state=result['state'],
        tax=result['tax'],
        pretotal=result['subtotal']+result['tax'],
        tips=result['tips'],
        total=result['total'],
        indpay=result['onesplit']
    )
    bot.reply_to(message, response_text)


@bot.message_handler(commands=['stock'])
def handling_stockinfo_message(message):
    logging.info(message)
    stringlists = re.sub('\s+', ' ', message.text).split(' ')[1:]
    if len(stringlists) <= 0:
        bot.reply_to(message, 'No stock symbol provided.')

    # find dates
    finddates_ls = [
        i
        for i, item in enumerate(map(lambda s: re.match('\d\d\d\d-[01]\d-\d\d', s), stringlists))
        if item is not None
    ]
    if len(finddates_ls) == 0:
        enddate = date.today().strftime('%Y-%m-%d')
        startdate = (date.today() - relativedelta(months=3)).strftime('%Y-%m-%d')
    elif len(finddates_ls) == 1:
        enddate = date.today().strftime('%Y-%m-%d')
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
    else:
        enddate = stringlists[finddates_ls[1]]
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
        try:
            datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(enddate))

    # find symbol
    remaining_indices = sorted(list(set(range(len(stringlists))) - set(finddates_ls)))
    symbol = stringlists[remaining_indices[0]]   # take only the first string as symbols
    symbol = symbol.upper()

    # calculate
    results = asyncio.run(get_symbol_inference(symbol, startdate, enddate, stockinfo_api_url))

    # wrangle message
    if 'message' in results.keys() and results['message'] == 'Internal server error':
        message_text = 'Unknown symbol: {}'.format(symbol)
    else:
        message_text = open(os.path.join('messagetemplates', 'stockinfo.txt')).read().format(
            symbol=symbol,
            r=results['r'],
            vol=results['vol'],
            downside_risk=results['downside_risk'],
            upside_risk=results['upside_risk'],
            beta=results['beta'] if results['beta'] is not None else np.nan,
            data_startdate=results['data_startdate'],
            data_enddate=results['data_enddate']
        )

    bot.reply_to(message, message_text)


@bot.message_handler(commands=['stockcorr'])
def handling_stockcorrelation_message(message):
    logging.info(message)
    stringlists = re.sub('\s+', ' ', message.text).split(' ')[1:]
    if len(stringlists) <= 1:
        bot.reply_to(message, 'Not enough stock symbols provided (at least 2).')

    # find dates
    finddates_ls = [
        i
        for i, item in enumerate(map(lambda s: re.match('\d\d\d\d-[01]\d-\d\d', s), stringlists))
        if item is not None
    ]
    if len(finddates_ls) == 0:
        enddate = date.today().strftime('%Y-%m-%d')
        startdate = (date.today() - relativedelta(months=3)).strftime('%Y-%m-%d')
    elif len(finddates_ls) == 1:
        enddate = date.today().strftime('%Y-%m-%d')
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
    else:
        enddate = stringlists[finddates_ls[1]]
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
        try:
            datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(enddate))

    # find symbol
    remaining_indices = sorted(list(set(range(len(stringlists))) - set(finddates_ls)))
    symbol1 = stringlists[remaining_indices[0]]
    symbol1 = symbol1.upper()
    symbol2 = stringlists[remaining_indices[1]]
    symbol2 = symbol2.upper()

    # calculate
    print('{}, {} from {} to {}'.format(symbol1, symbol2, startdate, enddate))
    results = asyncio.run(get_symbols_correlation(symbol1, symbol2, startdate, enddate, stockcorr_api_url))
    print(results)

    # wrangle message
    if 'message' in results.keys() and results['message'] == 'Internal server error':
        message_text = 'Error'
    else:
        message_text = open(os.path.join('messagetemplates', 'stockcorr.txt')).read().format(
            symbol1=symbol1,
            r1=results['r1'],
            vol1=results['std1'],
            r2=results['r2'],
            vol2=results['std2'],
            cov=results['cov'],
            corr=results['correlation'],
            data_startdate=startdate,
            data_enddate=enddate
        )

    bot.reply_to(message, message_text)


bot.polling()

## Time out message: {    "message": "Endpoint request timed out"}