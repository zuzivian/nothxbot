# -*- coding: utf-8 -*-

from ChatUtils import ChatUtils
from Game import Game

class GameManager(object):

    '''
    Manages all instances of waiting and active Games, including turn taking
    '''

    def __init__(self, chatutils: ChatUtils):
        self.games = []
        self.chatutils = chatutils

    def create_game(self):
        game = Game()
        self.games.append(game)
        return game

    def delete_game(self, game):
        for g in self.games:
            if g.id == game.id:
                return self.games.remove(g)

    def find_game_by_chat_id(self, chat_id):
        for g in self.games:
            for p in g.players:
              if p.chat_id == chat_id:
                return g

    def find_open_game(self):
        for g in self.games:
            if len(g.players) < 7 and g.turn == -1:
                return g

    def advance_game(self, game):
            # start game
            if game.turn == -1:
                game.turn = 0
                self.chatutils.broadcast_message(game, "Game has started!")

            # end of game, calculate score
            if game.get_top_card() == -1:
                self.chatutils.announce_winner(game)
                self.chatutils.announce_scores(game)
                self.delete_game(game)
                return

            if game.get_active_player().is_bot:
                # computer's turn
                move = game.decide_bot_action()
                self.chatutils.announce_player_action(game, move)
                game.make_player_move(move)
                self.advance_game(game)
            else:
                # request player action
                self.chatutils.send_game_summary(game, game.get_active_player().chat_id)
                self.chatutils.request_player_action(game)
