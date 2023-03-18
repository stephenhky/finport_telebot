
import json
import re
import os
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import asyncio
import urllib
from operator import itemgetter
import traceback
import sys

from dotenv import load_dotenv
import numpy as np
import telebot
import boto3

from finportbotutil.tipcalc import calculate_tips
from finportbotutil.syminfo import get_symbol_inference, get_symbols_correlation, get_plots_infos, search_symbols, get_ma_plots_info

logging.basicConfig(level=logging.INFO)

load_dotenv()

# Telebot API Key
api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key, threaded=False)

# Tip Calculator API
tipcalc_api_url = os.getenv('TIPCALCURL')

# Stock inference API
stockinfo_api_url = os.getenv('FININFO')
plotinfo_api_url = os.getenv('STOCKPLOT')
maplotinfo_api_url = os.getenv('MAPLOT')

# Stock correlation API
stockcorr_api_url = os.getenv('STOCKCORR')

# Search API
search_api_url = os.getenv('SEARCH')
modelloadretry = int(os.getenv('MODELLOADRETRY', 5))

# Add or Modify User ARN
addmodifyuser_arn = os.environ.get('ADDUSERARN')

# Symbol Search Wrapper ARN
searchwrappwer_arn = os.environ.get('SEARCHWRAPPERARN')

# commands
CMD_START = ['start']
CMD_HELP = ['help']
CMD_GREET = ['greet']
RE_HELLO = '[Hh]ello*'
RE_BYE = '[Bb]ye[!]?'
CMD_TIPS = ['tips']
CMD_STOCK = ['stock', 'stockg']
CMD_STOCKCORR = ['stockcorr']
CMD_SEARCH = ['search']
CMD_MA50 = ['stockgma50']
CMD_MA200 = ['stockgma200']
CMD_SP500_MA = ['sp500ma']


# polling flag
ispolling = False


def add_modify_user(message):
    lambda_client = boto3.client('lambda')
    try:
        lambda_client.invoke(
            FunctionName=addmodifyuser_arn,
            InvocationType='Event',
            Payload=json.dumps({
                'id': message.chat.id,
                'first_name': message.chat.first_name,
                'last_name': message.chat.last_name,
                'username': message.chat.username
            })
        )
    except AttributeError as e:
        print('The object "message" gives AttributeError!', file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise e


@bot.message_handler(commands=CMD_START)
def start(message):
    logging.info(message)
    print(message)
    start_msg = open('messagetemplates/start.txt', 'r').read()
    bot.send_message(message.chat.id, start_msg)
    return {'message': start_msg}


@bot.message_handler(commands=CMD_HELP)
def help(message):
    logging.info(message)
    print(message)
    help_msg = open('messagetemplates/help.txt', 'r').read()
    bot.reply_to(message, help_msg)
    return {'message': help_msg}


@bot.message_handler(commands=CMD_GREET)
def greet(message):
    logging.info(message)
    print(message)
    bot.reply_to(message, 'Hey, how is it going?')
    return {'message': 'Hey, how is it going?'}


@bot.message_handler(regexp=RE_HELLO)
def hello(message):
    logging.info(message)
    print(message)
    bot.send_message(message.chat.id, "Hello!")
    return {'message': "Hello!"}


@bot.message_handler(regexp=RE_BYE)
def sayonara(message):
    logging.info(message)
    print(message)
    bot.send_message(message.chat.id, "Have a nice day!")
    return {'message': "Have a nice day!"}


@bot.message_handler(commands=CMD_TIPS)
def handling_tips_command(message):
    logging.info(message)
    print(message)

    splitted_message = re.sub('\s+', ' ', message.text).split(' ')
    stringlists = splitted_message[1:]
    if len(stringlists) <= 0:
        bot.reply_to(message, 'No information provided!')
        return {'message': 'No information provided!'}
    try:
        subtotal = float(stringlists[0])
    except ValueError:
        bot.reply_to(message, 'Invalid subtotal: {}'.format(stringlists[0]))
        return {'message': 'Invalid subtotal: {}'.format(stringlists[0])}

    if len(stringlists) > 1:
        state = stringlists[1].upper()
        if state not in ['MD', 'VA', 'DC']:
            bot.reply_to(message, 'Only MD, VA, and DC are supported.')
            return {'message': 'Only MD, VA, and DC are supported.'}
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

    return {'message': response_text, 'result': result}


@bot.message_handler(commands=CMD_STOCK+CMD_MA50+CMD_MA200)
def handling_stockinfo_message(message):
    logging.info(message)
    print(message)

    splitted_message = re.sub('\s+', ' ', message.text).split(' ')
    stringlists = splitted_message[1:]
    if len(stringlists) <= 0:
        bot.reply_to(message, 'No stock symbol provided.')
        return {'message': 'No stock symbol provided.'}

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
            return {'message': 'Invalid date: {}'.format(startdate)}
    else:
        enddate = stringlists[finddates_ls[1]]
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
            return {'message': 'Invalid date: {}'.format(startdate)}
        try:
            datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(enddate))
            return {'message': 'Invalid date: {}'.format(enddate)}

    # find symbol
    remaining_indices = sorted(list(set(range(len(stringlists))) - set(finddates_ls)))
    symbol = stringlists[remaining_indices[0]]   # take only the first string as symbols
    symbol = symbol.upper()

    # calculate
    results = asyncio.run(get_symbol_inference(symbol, startdate, enddate, stockinfo_api_url))

    # wrangle message
    if 'message' in results.keys() and results['message'] == 'Internal server error':
        message_text = 'Unknown symbol: {}'.format(symbol)
        bot.reply_to(message, message_text)
        return {'message': message_text}
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
        return {
            'message': message_text,
            'result': results,
            'ploturl': plot_info['plot']['url']
        }
    elif splitted_message[0] == '/stockgma50' or splitted_message[0] =='/stockgma200':
        dayswindow = [50] if splitted_message[0] == '/stockgma50' else [200]
        plot_info = asyncio.run(get_ma_plots_info(symbol, startdate, enddate, dayswindow, maplotinfo_api_url))
        f = urllib.request.urlopen(plot_info['plot']['url'])
        bot.send_photo(message.chat.id, f, reply_to_message_id=message.id)
        return {
            'message': message_text,
            'result': results,
            'ploturl': plot_info['plot']['url']
        }
    else:
        return {
            'message': message_text,
            'result': results,
        }


@bot.message_handler(commands=CMD_STOCKCORR)
def handling_stockcorrelation_message(message):
    logging.info(message)
    print(message)

    stringlists = re.sub('\s+', ' ', message.text).split(' ')[1:]
    if len(stringlists) <= 1:
        bot.reply_to(message, 'Not enough stock symbols provided (at least 2).')
        return {'message': 'Not enough stock symbols provided (at least 2).'}

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
            return {'message': 'Invalid date: {}'.format(startdate)}
    else:
        enddate = stringlists[finddates_ls[1]]
        startdate = stringlists[finddates_ls[0]]
        try:
            datetime.strptime(startdate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(startdate))
            return {'message': 'Invalid date: {}'.format(startdate)}
        try:
            datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError:
            bot.reply_to(message, 'Invalid date: {}'.format(enddate))
            return {'message': 'Invalid date: {}'.format(enddate)}

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
    return {'message': message_text, 'result': results}


@bot.message_handler(commands=CMD_SEARCH)
def handling_search(message):
    logging.info(message)
    print(message)

    if ispolling:
        querystring = message.text[8:].strip()
        logging.info('query string: {}'.format(querystring))
        print('query string: {}'.format(querystring))
        for i in range(modelloadretry):
            results = asyncio.run(search_symbols(querystring, search_api_url))
            if 'message' in results and 'timed out' in results['message']:
                logging.info('Trial {} fail'.format(i))
                print('Trial {} fail'.format(i))
                bot.reply_to(message, 'Model loading...')
            elif 'queryresults' in results:
                break
            else:
                logging.info('Trial {} fail with error'.format(i))
                print('Trial {} fail with error'.format(i))
                bot.reply_to(message, 'Unknown error; retrying...')
        logging.info(results)
        print(results)
        if 'queryresults' not in results:
            bot.reply_to(message, 'Unknown error.')
            return {'message': 'Unknown error.'}
        else:
            symbol_and_descp = [
                symbolprob['symbol'] + ' : ' + symbolprob['descp']
                for symbolprob in sorted(results['queryresults'], key=itemgetter('prob'), reverse=True)
            ]
            bot.reply_to(message, '\n'.join(symbol_and_descp))
            return {
                'message': '\n'.join(symbol_and_descp),
                'result': results
            }
    else:
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName=searchwrappwer_arn,
            InvocationType='Event',
            Payload=json.dumps(message.json)
        )
        return {'message': None, 'comment': 'Search done using another Lambda'}


@bot.message_handler(commands=CMD_SP500_MA)
def plotting_sp500_ma(message):
    enddate = date.today().strftime('%Y-%m-%d')
    startdate = (date.today() - relativedelta(years=1)).strftime('%Y-%m-%d')
    plot_info = asyncio.run(get_ma_plots_info('^GSPC', startdate, enddate, [50, 200], maplotinfo_api_url, title='S&P 500 (^GSPC)'))
    f = urllib.request.urlopen(plot_info['plot']['url'])
    bot.send_photo(message.chat.id, f, reply_to_message_id=message.id)
    return {
        'ploturl': plot_info['plot']['url']
    }


def lambda_handler(event, context):
    message = json.loads(event['body'])
    logging.info(message)
    print(message)
    if message.get('polling', False):
        ispolling = True
        bot.polling()
        return {
            'statusCode': 200,
            'body': json.dumps({'approach': 'polling'})
        }
    else:
        update = telebot.types.Update.de_json(message)
        logging.info(update)
        print(update)
        message = update.message
        try:
            add_modify_user(message)
        except AttributeError:
            pass

        try:
            bot.process_new_messages([message])
            print('Processed.')
            return {
                'statusCode': 200,
                'body': json.dumps({'approach': 'webhook'})
            }
        except AttributeError:
            print('Telegram error.', file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return {
                'statusCode': 200,
                'body': json.dumps({'approach': 'webhook'})
            }


if __name__ == '__main__':
    ispolling = True
    bot.polling()

# Reference: how to set up webhook: https://aws.plainenglish.io/develop-your-telegram-chatbot-with-aws-api-gateway-dynamodb-lambda-functions-410dcb1fb58a
## Time out message: {    "message": "Endpoint request timed out"}