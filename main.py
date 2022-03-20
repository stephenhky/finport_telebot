
import os
import telebot
import logging


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


@bot.message_handler(regexp='[Bb]ye')
def sayonara(message):
    logging.info(message)
    bot.send_message(message.chat.id, "Have a nice day!")


bot.polling()
