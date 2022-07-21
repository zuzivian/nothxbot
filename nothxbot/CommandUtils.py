# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import CallbackContext

from GameManager import GameManager
from ChatUtils import ChatUtils

class CommandUtils(object):

    '''
    Contains methods for handling telegram commands and callback queries
    '''

    def __init__(self, manager: GameManager, chatutils: ChatUtils):
        self.manager = manager
        self.chatutils = chatutils

    def start(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Hi player, type /join to start a game!') 

    def join(self, update: Update, context: CallbackContext):
        if self.manager.find_game_by_chat_id(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id, text='You are already in a game!') 
        elif self.manager.find_open_game():
            game = self.manager.find_open_game()
            name = self.chatutils.get_username(update.message.from_user)
            game.add_player(update.message.from_user.id, update.effective_chat.id, name)
            self.chatutils.announce_game_lobby(game)
        else:
            user = update.message.from_user
            name = self.chatutils.get_username(user)
            game = self.manager.create_game()
            game.add_player(user.id, update.effective_chat.id, name)
            self.chatutils.announce_game_lobby(game)

    def leave(self, update: Update, context: CallbackContext):
        game = self.manager.find_game_by_chat_id(update.effective_chat.id)
        if not game:         
            return context.bot.send_message(chat_id=update.effective_chat.id, text='You are not in a game!') 
        user = update.message.from_user
        name = self.chatutils.get_username(user)
        if game.turn == -1:
            # game hasn't started
            game.remove_player(name)
        else:
            # game already started, convert to bot
            game.get_player_by_id(user.id).change_to_bot()
            self.manager.advance_game(game)
        if game.num_humans() == 0:
            self.manager.delete_game(game)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Left the game!')

    def scores(self, update: Update, context: CallbackContext):
        game = self.manager.find_game_by_chat_id(update.effective_chat.id)
        if game:
            return self.chatutils.announce_scores(game)      
        context.bot.send_message(chat_id=update.effective_chat.id, text='You are not in a game!') 

    def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        game = self.manager.find_game_by_chat_id(update.effective_chat.id)
        if not game:
            return
        if query.data == "ADDBOT" and game.turn == -1 and len(game.players) < 7:
            game.add_player()
            self.chatutils.announce_game_lobby(game)
        elif query.data == "SUBBOT" and game.turn == -1 and game.num_bots() != 0:
            for p in reversed(game.players):
                if p.is_bot:
                    game.remove_player(p.name)
                    break
            self.chatutils.announce_game_lobby(game)
        elif query.data == "START" and len(game.players) >= 3 and game.turn == -1:
            query.delete_message()
            self.manager.advance_game(game)
        elif query.data == "TAKE" or query.data == "PASS" and game.turn != -1:
            query.delete_message()
            if query.from_user.id == game.get_active_player().player_id:
                self.chatutils.announce_player_action(game, query.data)
                game.make_player_move(query.data)
                self.manager.advance_game(game)
