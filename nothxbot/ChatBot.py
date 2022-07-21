# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import os

from CommandUtils import CommandUtils
from ChatUtils import ChatUtils
from GameManager import GameManager

class ChatBot(object):

    '''
    Handles all aspects of operating the telegram bot, including interfacing with the Telegram bot API.
    '''

    def __init__(self, token: str):
        self.token = token
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.chatutils = ChatUtils(self.dispatcher)
        self.manager = GameManager(self.chatutils)
        self.cmdutils = CommandUtils(self.manager, self.chatutils)

    def run(self, mode):
        self.init_handlers()
        if mode == "POLL":
            self.updater.start_polling()
            self.updater.idle()
        elif mode == "WEBHOOK":
            PORT = int(os.environ.get('PORT', '8443'))
            self.updater.start_webhook(listen="0.0.0.0",
                                  port=PORT,
                                  url_path=self.token,
                                  webhook_url="https://nothxbot.herokuapp.com/" + self.token)
            #self.updater.bot.set_webhook("https://nothxbot.herokuapp.com/" + self.token)
            self.updater.idle()

    def init_handlers(self):
        self.dispatcher.add_handler(CommandHandler('start', self.cmdutils.start))
        self.dispatcher.add_handler(CommandHandler('join', self.cmdutils.join))
        self.dispatcher.add_handler(CommandHandler('leave', self.cmdutils.leave))
        self.dispatcher.add_handler(CommandHandler('scores', self.cmdutils.scores))
        self.dispatcher.add_handler(CallbackQueryHandler(self.cmdutils.button_handler))
