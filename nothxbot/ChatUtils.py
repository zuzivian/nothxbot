# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher

class ChatUtils(object):
    
    '''
    Contains methods that interact between game instances and the Telegram bot API.
    '''

    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher

    def announce_game_lobby(self, game):
        text = "Game Lobby (3-7 players to start)\n\nPlayers:\n"
        for p in game.players:
            text += "{}\n".format(p.name)
        keyboard = [[
            InlineKeyboardButton("+Bot", callback_data="ADDBOT"),
            InlineKeyboardButton("-Bot", callback_data="SUBBOT"),
            InlineKeyboardButton("Start", callback_data="START")
            ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if game.players[0].last_msg_id:
            return self.edit_broadcast(game, text, reply_markup=reply_markup)
        else:
            return self.broadcast_message(game, text, reply_markup=reply_markup)

    def announce_player_action(self, game, move):
        text = "\U000025B6 {}: {} on card {} [Pot: {}]".format(game.get_active_player().name, move, game.get_top_card(), game.pot)
        return self.broadcast_message(game, text)

    def send_game_summary(self, game, chat_id):
        text = ""
        for p in game.players:
            text += "{}: {}\n".format(p.name, p.hand)
        text += "\n\U0001F0CF No. {}\n\U0001FA99 {} tokens".format(game.get_top_card(), game.pot)
        return self.dispatcher.bot.send_message(chat_id=chat_id, text=text)

    def request_player_action(self, game):
        player = game.get_active_player()
        keyboard = [[InlineKeyboardButton("TAKE", callback_data="TAKE")]]
        if player.tokens > 0:
            keyboard[0].append(InlineKeyboardButton("PASS", callback_data="PASS"))
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "\U00002757 Your turn! You have {} tokens. \U00002757".format(player.tokens)
        return self.dispatcher.bot.send_message(chat_id=player.chat_id, text=text, reply_markup=reply_markup)

    def announce_scores(self, game):
        scores = game.compute_scores()
        text = "Scores:\n"
        for i in range(len(game.players)):
            text += "{}: {}\n".format(game.players[i].name, scores[i])
        return self.broadcast_message(game, text)

    def announce_winner(self, game):
        scores = game.compute_scores()
        winner = game.players[scores.index(min(scores))] 
        text = "Game over. {} is the winner!".format(winner.name)
        return self.broadcast_message(game, text)

    def get_username(self, user):
         return user.username if user.username else user.first_name

    def broadcast_message(self, game, text, **kwargs):
        for p in game.players:
            if p.chat_id:
                msg = self.dispatcher.bot.send_message(chat_id=p.chat_id, text=text, **kwargs)
                p.last_msg_id = msg.message_id

    def edit_broadcast(self, game, text, **kwargs):
        for p in game.players:
            if p.chat_id:
                if p.last_msg_id:
                    msg = self.dispatcher.bot.edit_message_text(message_id=p.last_msg_id, chat_id=p.chat_id, text=text, **kwargs)
                else:
                    msg = self.dispatcher.bot.send_message(chat_id=p.chat_id, text=text, **kwargs)
                p.last_msg_id = msg.message_id

