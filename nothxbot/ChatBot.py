# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, CallbackQueryHandler
import uuid, logging, random, os

class ChatBot(object):

    '''
    Handles all aspects of operating the telegram bot, 
    including interfacing with the python-telegram-bot API.
    '''

    def __init__(self, token: str):
        self.token = token
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.manager = GameManager()
        self.chatutils = ChatUtils(self.manager, self.dispatcher)
        self.cmdutils = CommandUtils(self.manager, self.chatutils)

    def run(self, mode):
        self.initCommandHandlers()
        self.initCallbackHandlers()
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

    def initCommandHandlers(self):
        self.dispatcher.add_handler(CommandHandler('start', self.cmdutils.start))
        self.dispatcher.add_handler(CommandHandler('join', self.cmdutils.join))
        self.dispatcher.add_handler(CommandHandler('leave', self.cmdutils.leave))
        self.dispatcher.add_handler(CommandHandler('scores', self.cmdutils.scores))

    def initCallbackHandlers(self):
        self.dispatcher.add_handler(CallbackQueryHandler(self.chatutils.button_handler))


class CommandUtils(object):

    '''
    Contains methods for handling the various telegram commands
    '''

    def __init__(self, manager, chatutils):
        self.manager = manager
        self.chatutils = chatutils

    def start(self, update: Update, context: CallbackContext):
        self.send_message(chat_id=update.effective_chat.id, text='Hi player, type /join to start a game!') 

    def join(self, update: Update, context: CallbackContext):
        if self.manager.find_game_by_chat_id(update.effective_chat.id):
            self.chatutils.send_message(chat_id=update.effective_chat.id, text='You are already in a game!') 
        elif self.manager.find_open_game():
            game = self.manager.find_open_game()
            user = update.message.from_user
            name = self.chatutils.get_username(user)
            game.add_player(user.id, update.effective_chat.id, name)
            self.chatutils.announce_game_lobby(game.id)
        else:
            user = update.message.from_user
            name = self.chatutils.get_username(user)
            game = self.manager.create_game()
            game.add_player(user.id, update.effective_chat.id, name)
            self.chatutils.announce_game_lobby(game.id)

    def leave(self, update: Update, context: CallbackContext):
        game = self.manager.find_game_by_chat_id(update.effective_chat.id)
        if not game:         
            return context.bot.send_message(chat_id=update.effective_chat.id, text='You are not in a game!') 
        user = update.message.from_user
        name = self.chatutils.get_username(user)
        if game.turn == -1:
            game.remove_player(name)
        else:
            player = game.get_player_by_id(user.id)
            player.change_to_bot()
            self.chatutils.advance_game(game.id)
        if game.number_of_humans() == 0:
            self.manager.delete_game(game.id)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Left the game!')

    def scores(self, update: Update, context: CallbackContext):
        game = self.manager.find_game_by_chat_id(update.effective_chat.id)
        if game:
            self.chatutils.announce_scores(game.id)
            return
        context.bot.send_message(chat_id=update.effective_chat.id, text='You are not in a game!') 

class ChatUtils(object):
    
    '''
    Contains methods that interact between game instances and the telegram bot
    '''

    def __init__(self, manager, dispatcher):
        self.manager = manager
        self.dispatcher = dispatcher

    def advance_game(self, game_id):
        game = self.manager.find_game_by_game_id(game_id)

        # start game
        if game.turn == -1:
            game.turn = 0
            self.broadcast_message(game.id, "Game has started!")

        # end of game, calculate score
        if game.get_top_card() == -1:
            self.announce_winner(game.id)
            self.announce_scores(game.id)
            self.manager.delete_game(game.id)
            return

        # get current active player
        player = game.get_active_player()

        if player.is_bot:
            # computer's turn
            top = game.get_top_card()
            move = random.choices(["TAKE", "PASS"], weights=[game.pot+1, top*2])[0]
            if player.has_consecutive_card(top):
                move = random.choices(["TAKE", "PASS"], weights=[game.pot+1, top/2])[0]
            if top < game.pot + 1:
                move = "TAKE"
            self.announce_player_action(game_id, move)
            game.make_player_move(move)
            self.advance_game(game_id)
        
        else:
            # request player action
            self.send_game_summary(player.chat_id)
            self.request_player_action(game.id)

    def announce_game_lobby(self, game_id):
        game = self.manager.find_game_by_game_id(game_id)
        text = "Game Lobby (2-7 players to start)\n\nPlayers:\n"
        for p in game.players:
            text += "{}\n".format(p.name)
        keyboard = [[
            InlineKeyboardButton("+Bot", callback_data="ADDBOT"),
            InlineKeyboardButton("-Bot", callback_data="SUBBOT"),
            InlineKeyboardButton("Start", callback_data="START")
            ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return self.broadcast_message(game_id, text, reply_markup=reply_markup)

    def announce_player_action(self, game_id, move):
        game = self.manager.find_game_by_game_id(game_id)
        text = "\U000025B6 {}: {} on card {} [Pot: {}]".format(game.get_active_player().name, move, game.get_top_card(), game.get_pot())
        return self.broadcast_message(game_id, text)

    def send_game_summary(self, chat_id):
        game = self.manager.find_game_by_chat_id(chat_id)
        text = ""
        for p in game.players:
            text += "{}: {}\n".format(p.name, p.hand)
        text += "\n\U0001F0CF No. {}\n\U0001FA99 {} tokens".format(game.get_top_card(), game.get_pot())
        return self.send_message(chat_id=chat_id, text=text)

    def request_player_action(self, game_id):
        game = self.manager.find_game_by_game_id(game_id)
        player = game.get_active_player()
        tokens = game.get_player_tokens(player_id=player.player_id)
        keyboard = [[InlineKeyboardButton("TAKE", callback_data="TAKE")]]
        if tokens > 0:
            keyboard[0].append(InlineKeyboardButton("PASS", callback_data="PASS"))
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "\U00002757 Your turn! You have {} tokens. \U00002757".format(tokens)
        return self.send_message(chat_id=player.chat_id, text=text, reply_markup=reply_markup)

    def announce_scores(self, game_id):
        game = self.manager.find_game_by_game_id(game_id)
        scores = game.compute_scores()
        text = "Scores:\n"
        for i in range(len(game.players)):
            text += "{}: {}\n".format(game.players[i].name, scores[i])
        return self.broadcast_message(game_id, text)

    def announce_winner(self, game_id):
        game = self.manager.find_game_by_game_id(game_id)
        scores = game.compute_scores()
        win_index = scores.index(min(scores))
        winner = game.players[win_index] 
        text = "Game over. {} is the winner!".format(winner.name)
        return self.broadcast_message(game_id, text)

    def get_username(self, user):
         return user.username if user.username else user.first_name

    def send_message(self, chat_id, text, **kwargs):
        return self.dispatcher.bot.send_message(chat_id=chat_id, text=text, **kwargs)

    def broadcast_message(self, game_id, text, **kwargs):
        game = self.manager.find_game_by_game_id(game_id)
        for p in game.players:
            if p.chat_id:
                self.dispatcher.bot.send_message(chat_id=p.chat_id, text=text, **kwargs)
    
    def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        chat_id = update.effective_chat.id
        game = self.manager.find_game_by_chat_id(chat_id)
        if query.data == "ADDBOT":
            if len(game.players) < 7:
                game.add_player()
                query.delete_message()
                self.announce_game_lobby(game.id)
        elif query.data == "SUBBOT":
            if game.get_last_bot():
                game.remove_player(game.get_last_bot().name)
            query.delete_message()
            self.announce_game_lobby(game.id)
        elif query.data == "START":
            if len(game.players) >= 2:
                query.delete_message()
                self.advance_game(game.id)
        elif query.data == "TAKE" or query.data == "PASS":
            query.delete_message()
            self.announce_player_action(game.id, query.data)
            game.make_player_move(query.data)
            self.advance_game(game.id)


class GameManager(object):

    def __init__(self):
        self.games = []

    def create_game(self):
        game = Game()
        self.games.append(game)
        return game

    def delete_game(self, id: str):
        for g in self.games:
            if g.id == id:
                self.games.remove(g)
                logging.info('Game #{} removed.'.format(id))
                return True
        logging.warning('Game #{} not found, could not remove.'.format(id))
        return False

    def find_game_by_player_id(self, player_id):
        for g in self.games:
            for p in g.players:
              if p.player_id == player_id:
                return g

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

class Game(object):

    def __init__(self):
        self.id = uuid.uuid1()
        self.players = []
        self.deck = self.create_shuffled_deck()
        self.turn = -1
        self.pot = 0
        logging.info('Game #{} created.'.format(self.id))

    def create_shuffled_deck(self):
        deck = list(range(3,35))
        random.shuffle(deck)
        deck = deck[:-9]
        logging.info(deck)
        return deck     

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

    def get_pot(self):
        return self.pot

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

    def make_player_move(self, move):
        player = self.players[self.turn]
        if player.tokens <= 0:
            move = "TAKE"
        logging.info("Player {} action: {}".format(self.turn, move))
        if move == "PASS":
            player.remove_tokens(1)
            self.pot += 1
            self.turn = (self.turn + 1) % len(self.players)
        else:
            player.add_tokens(self.pot)
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
                    logging.debug(hand[i], hand[i+1])
                    continue
                score += hand[i]
            scores.append(score)
        return scores


class Player(object):

    def __init__(self, player_id=None, chat_id=None, player_name=None):
        self.is_bot = not isinstance(player_id, int)
        self.chat_id = chat_id
        self.player_id = player_id
        self.hand = []
        self.tokens = 11
        self.name = player_name if player_name else "Bot" + str(uuid.uuid1().int)[-5:-2]

    def has_consecutive_card(self, number: int):
        for card in self.hand:
            if card == number + 1 or card == number - 1:
                return True
        return False

    def add_tokens(self, count):
        self.tokens += count
        return self.tokens

    def remove_tokens(self, count):
        self.tokens -= count
        return self.tokens

    def change_to_bot(self):
        self.is_bot = True
        self.chat_id = None
        self.player_id = None
        self.name += "Bot"
    
