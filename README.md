# No Thanks Bot
========================

A Telegram bot that allows users to play No Thanks!, a popular board game

#### Author: Nathaniel Wong

#### Version: 0.0.3

# Rules of the Game

The game is played with a deck of 32 unique cards, each valued 3 to 35. 
To prepare the deck, 9 cards are removed from deck and the rest are shuffled. 
The game begins with the top card placed face-up.

Play runs clockwise. During each player's turn, a player has only two options:
- play a token to avoid collecting the current face-up card
- collecting the face-up card (along with any tokens that have already been played on that card) and turn over the next card face up

At the end of the game, the lowest-scoring player wins. Scores are calculated based on the following rules:
- each card is worth its face value
- if there is a chain of consective cards, the player may only count the lowest of the chain
- the number of tokens are subtracted from the total score

# Try the bot

Link to the live version of the bot on telegram: http://t.me/nothxbot

## Changelog

### 0.0.3
- refactored ChatBot.py into multiple files
- removed redundant methods
- bugfix: wrong computation of some scores

### 0.0.2
- refactored ChatBot, ChatUtil and GameManager
- bugfix: player could add and remove bots during game
- bugfix: player could TAKE or PASS out of turn

### 0.0.1
- initial No Thx! build with multiplayer and AI players
- created chat-related classes: ChatBot, CommandUtils, ChatUtils
- created game-related classes: GameManager, Game, Player
