# -*- coding: utf-8 -*-

import uuid


class Player(object):

    '''
    Defines a human or bot player
    '''

    def __init__(self, player_id=None, chat_id=None, player_name=None):
        self.is_bot = not isinstance(player_id, int)
        self.chat_id = chat_id
        self.player_id = player_id
        self.last_msg_id = None
        self.hand = []
        self.tokens = 11
        self.name = player_name if player_name else "Bot" + str(uuid.uuid1().int)[-5:-2]

    def has_consecutive_card(self, number: int):
        for card in self.hand:
            if card == number + 1 or card == number - 1:
                return True
        return False

    def change_to_bot(self):
        self.is_bot = True
        self.chat_id = None
        self.player_id = None
        self.name += "Bot"

    def compute_score(self):
        score = -self.tokens
        for i in reversed(range(len(self.hand))):
            if i > 0 and self.hand[i] - self.hand[i-1] == 1:
                continue
            score += self.hand[i]
        return score