# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, CallbackQueryHandler
import uuid, random, os

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


class CommandUtils(object):

    '''
    Contains methods for handling telegram commands and callback queries
    '''

    def __init__(self, manager, chatutils):
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
            player = game.get_player_by_id(user.id)
            player.change_to_bot()
            self.manager.advance_game(game)
        if game.number_of_humans() == 0:
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
        elif query.data == "SUBBOT" and game.turn == -1 and game.get_last_bot():
            game.remove_player(game.get_last_bot().name)
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

class ChatUtils(object):
    
    '''
    Contains methods that interact between game instances and the Telegram bot API.
    '''

    def __init__(self, dispatcher):
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
        return self.send_message(chat_id=chat_id, text=text)

    def request_player_action(self, game):
        player = game.get_active_player()
        tokens = game.get_player_tokens(player_id=player.player_id)
        keyboard = [[InlineKeyboardButton("TAKE", callback_data="TAKE")]]
        if tokens > 0:
            keyboard[0].append(InlineKeyboardButton("PASS", callback_data="PASS"))
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "\U00002757 Your turn! You have {} tokens. \U00002757".format(tokens)
        return self.send_message(chat_id=player.chat_id, text=text, reply_markup=reply_markup)

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

    def send_message(self, chat_id, text, **kwargs):
        return self.dispatcher.bot.send_message(chat_id=chat_id, text=text, **kwargs)

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



class GameManager(object):

    def __init__(self, chatutils):
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

    def find_game_by_game_id(self, game_id):
        for g in self.games:
            if g.id == game_id:
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

class Game(object):

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

    def number_of_humans(self):
        count = 0
        for p in self.players:
            if not p.is_bot:
                count += 1
        return count

    def get_last_bot(self):
        for p in reversed(self.players):
            if p.is_bot:
                return p

    def get_player_tokens(self, player_id=None, position=None):
        if position:
            return self.players[position].tokens
        for p in self.players:
            if p.player_id == player_id:
                return p.tokens

    def get_player_hand(self, player_id=None, position=None):
        if position:
            return self.players[position].hand
        for p in self.players:
            if p.player_id == player_id:
                return p.hand

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
            score = -p.tokens
            hand = p.hand
            hand.sort(reverse=True)
            for i in range(len(hand)):
                if i+1 < len(hand) and hand[i] - hand[i+1] == 1:
                    continue
                score += hand[i]
            scores.append(score)
        return scores


class Player(object):

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
    
