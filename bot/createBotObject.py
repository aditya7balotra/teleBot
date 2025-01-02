import telebot
from dotenv import load_dotenv
import os
from log import logging


load_dotenv('env/.env')
botLog = logging.getLogger('create bot')


# initializing the TeleBot class
try:
    bot = telebot.TeleBot(os.getenv('bot_api'), parse_mode=None)
    botLog.info('TeleBot class initialized successfully')
except:
    botLog.critical('Telebot class not initialised properly', exc_info= True)
    exit()
    