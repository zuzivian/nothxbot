#!/usr/bin/env python3

from ChatBot import ChatBot
import logging

'''
testbot.py

Top-level bot script that initiates amd ChatBot() object and begins
serving requests via webhook or polling.

'''

def main():
    # python-telegram-bot provides logging features for debugging purposes
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)

    # provide TOKEN to initiate ChatBot
    TOKEN = ''
    bot = ChatBot(TOKEN)
    bot.run("POLL")


if __name__ == "__main__":
    main()
