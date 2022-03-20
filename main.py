
import os
import telebot

api_key = os.getenv('API_KEY')
bot = telebot.TeleBot(api_key)


@bot.message_handler(commands=['Hello'])
def greet(message):
    bot.reply_to_user(message, 'How is it going?')


bot.polling()
