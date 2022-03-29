
import re
import os
import logging

import telebot

from finportbotutil.tipcalc import get_tipargparser, calculate_tips

logging.basicConfig(level=logging.INFO)


# Telebot API Key
api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key)

# Tip Calculator API
tipcalc_api_url = os.getenv('TIPCALCURL')


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
