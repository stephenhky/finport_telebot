
import re
import os
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import asyncio
import urllib

from dotenv import load_dotenv
import numpy as np
import telebot

from finportbotutil.tipcalc import calculate_tips
from finportbotutil.syminfo import get_symbol_inference, get_symbols_correlation, get_plots_infos

logging.basicConfig(level=logging.INFO)

load_dotenv()

# Telebot API Key
api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key)

# Tip Calculator API
tipcalc_api_url = os.getenv('TIPCALCURL')

# Stock inference API
stockinfo_api_url = os.getenv('FININFO')
plotinfo_api_url = os.getenv('STOCKPLOT')

# Stock correlation API
stockcorr_api_url = os.getenv('STOCKCORR')

# Search API
search_api_url = os.getenv('SEARCH')


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


@bot.message_handler(commands=['tips'])
def handling_tips_command(message):
    logging.info(message)
    splitted_message = re.sub('\s+', ' ', message.text).split(' ')
    stringlists = splitted_message[1:]
    if len(stringlists) <= 0:
        bot.reply_to(message, 'No information provided!')
        return

    try:
        subtotal = float(stringlists[0])
    except ValueError:
        bot.reply_to(message, 'Invalid subtotal: {}'.format(stringlists[0]))
        return

    if len(stringlists) > 1:
        state = stringlists[1].upper()
        if state not in ['MD', 'VA', 'DC']:
            bot.reply_to(message, 'Only MD, VA, and DC are supported.')
            return
    else:
        state = 'MD'
        bot.reply_to(message, 'Assumed in MD.')

    if len(stringlists) > 2:
        try:
            split = int(stringlists[2])
        except ValueError:
            split = 1
    else:
        split = 1

    result = calculate_tips(subtotal, state, split, tipcalc_api_url)

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


@bot.message_handler(commands=['stock', 'stockg'])
def handling_stockinfo_message(message):
    logging.info(message)
    splitted_message = re.sub('\s+', ' ', message.text).split(' ')
    stringlists = splitted_message[1:]
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

    if splitted_message[0] == '/stockg':
        plot_info = asyncio.run(get_plots_infos(symbol, startdate, enddate, plotinfo_api_url))
        f = urllib.request.urlopen(plot_info['plot']['url'])
        bot.send_photo(message.chat.id, f, reply_to_message_id=message.id)


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
            symbol2=symbol2,
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


def handling_search(message):
    pass


bot.polling()

## Time out message: {    "message": "Endpoint request timed out"}