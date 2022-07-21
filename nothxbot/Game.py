# -*- coding: utf-8 -*-

import uuid, random
from Player import Player


class Game(object):

    '''
    Instance of a NoThx game with players and card deck
    '''

    def __init__(self):
        self.id = uuid.uuid1()
        self.players = []
        self.deck = self.create_shuffled_deck()
        self.turn = -1
        self.pot = 0

    def create_shuffled_deck(self):
        deck = list(range(3,35))
        random.shuffle(deck)
        return deck[:-9]

    def get_top_card(self):
        if len(self.deck) == 0:
            return -1
        return self.deck[-1]

    def add_player(self, player_id=None, chat_id=None, player_name=None):
        return self.players.append(Player(player_id, chat_id, player_name))

    def remove_player(self, player_name):
        for i, p in enumerate(self.players):
            if p.name == player_name:
                del self.players[i]
                return p

    def num_humans(self):
        count = 0
        for p in self.players:
            count += 1 if not p.is_bot else 0
        return count

    def num_bots(self):
        count = 0
        for p in self.players:
            count += 1 if p.is_bot else 0
        return count

    def get_active_player(self):
        return self.players[self.turn]

    def get_player_by_id(self, player_id):
        for p in self.players:
            if p.player_id == player_id:
                return p

    def decide_bot_action(self):
        player = self.get_active_player()
        top = self.get_top_card()
        if top < self.pot + 1 or not player.is_bot:
            move = "TAKE"
        elif player.has_consecutive_card(top):
            move = random.choices(["TAKE", "PASS"], weights=[self.pot+1, top/2])[0]
        else:
            move = random.choices(["TAKE", "PASS"], weights=[self.pot+1, top*2])[0]
        return move

    def make_player_move(self, move):
        player = self.get_active_player()
        if player.tokens <= 0:
            move = "TAKE"
        if move == "PASS":
            player.tokens -= 1
            self.pot += 1
            self.turn = (self.turn + 1) % len(self.players)
        else:
            player.tokens += self.pot
            self.pot = 0
            player.hand.append(self.deck.pop())
            player.hand.sort()
        return move

    def compute_scores(self):
        scores = []
        for p in self.players:
            scores.append(p.compute_score())
        return scores
