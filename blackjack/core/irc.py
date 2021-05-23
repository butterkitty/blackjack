#!/usr/bin/env python
# BlackJack IRC Bot - Developed by butterkitty in Python, based on acidvegas' bot (https://acid.vegas/blackjack)
# irc.py

import inspect
import os
import random
import socket
import ssl
import threading
import time

import config
import debug

# Data Directories & Files (DO NOT EDIT)
data_dir   = os.path.join(os.path.dirname(os.path.realpath(inspect.stack()[-1][1])), 'data')
cheat_file = os.path.join(data_dir, 'cheat.txt')
help_file  = os.path.join(data_dir, 'help.txt')

# Card Types
club	= ('♣','clubs')
diamond = ('♦','diamonds')
heart   = ('♥','hearts')
spade   = ('♠','spades')

# Deck Table (Name, ASCII, Value, Remaining Suits)
deck = {
	'ace'   : [None, 11, [club,diamond,heart,spade]],
	'two'   : [None, 2,  [club,diamond,heart,spade]],
	'three' : [None, 3,  [club,diamond,heart,spade]],
	'four'  : [None, 4,  [club,diamond,heart,spade]],
	'five'  : [None, 5,  [club,diamond,heart,spade]],
	'six'   : [None, 6,  [club,diamond,heart,spade]],
	'seven' : [None, 7,  [club,diamond,heart,spade]],
	'eight' : [None, 8,  [club,diamond,heart,spade]],
	'nine'  : [None, 9,  [club,diamond,heart,spade]],
	'ten'   : [None, 10, [club,diamond,heart,spade]],
	'jack'  : [None, 10, [club,diamond,heart,spade]],
	'queen' : [None, 10, [club,diamond,heart,spade]],
	'king'  : [None, 10, [club,diamond,heart,spade]]
}

# Formatting Control Characters / Color Codes
bold        = '\x02'
italic      = '\x1D'
underline   = '\x1F'
reverse     = '\x16'
reset       = '\x0f'
white       = '00'
black       = '01'
blue        = '02'
green       = '03'
red         = '04'
brown       = '05'
purple      = '06'
orange      = '07'
yellow      = '08'
light_green = '09'
cyan        = '10'
light_cyan  = '11'
light_blue  = '12'
pink        = '13'
grey        = '14'
light_grey  = '15'

def color(msg, foreground, background=None):
	if background:
		return '\x03{0},{1}{2}{3}'.format(foreground, background, msg, reset)
	else:
		return '\x03{0}{1}{2}'.format(foreground, msg, reset)

class IRC(object):
	def __init__(self):
		self.player_ace_minus = 0
		self.dealer_ace_minus = 0
		self.player_hand      = []
		self.dealer_hand	= []
		self.last_move = 0
		self.last_time = 0
		self.player    = None
		self.player_total     = 0
		self.dealer_total	= 0
		self.mini_deck  = config.settings.mini_deck #Full size not currently working
		self.sock       = None
		self.username	= config.ident.username

	def action(self, chan, msg):
		self.sendmsg(chan, '\x01ACTION {0}\x01'.format(msg))

	def connect(self):
		try:
			self.create_socket()
			self.sock.connect((config.connection.server, config.connection.port))
			if config.login.network:
				self.raw('PASS ' + config.login.network)
			self.raw('USER {0} 0 * :{1}'.format(config.ident.username, config.ident.realname))
			self.raw('NICK ' + config.ident.nickname)
		except socket.error as ex:
			debug.error('Failed to connect to IRC server.', ex)
			self.event_disconnect()
		else:
			self.listen()

	def create_socket(self):
		family	= socket.AF_INET6 if config.connection.ipv6 else socket.AF_INET
		self.sock = socket.socket(family, socket.SOCK_STREAM)
		if config.connection.vhost:
			self.sock.bind((config.connection.vhost, 0))
		if config.connection.ssl:
			self.sock = ssl.wrap_socket(self.sock)

	def draw(self, dealer=False):
		card_type = random.choice(list(deck.keys()))
		remaining = deck[card_type][2]
		while not remaining:
			card_type = random.choice(list(deck.keys()))
			remaining = deck[card_type][2]
		card_suit = random.choice(remaining)
		if card_suit in (heart,diamond):
			card_color = red
		else:
			card_color = black
		card_value = deck[card_type][1]
		if self.mini_deck:
			card = deck[card_type][0].replace('X', card_suit[0])
			card = color(card, card_color, white)
			if (not dealer): self.player_hand.append(card)
			else: self.dealer_hand.append(card)
		else:
			for i in range(5):
				card = deck[card_type][0][i].replace('X', card_suit[0])
				card = color(card, card_color, white)
				if (not dealer): self.player_hand[i].append(card)
				else: self.dealer_hand[i].append(card)
		deck[card_type][2].remove(card_suit)
		if (not dealer): 
#			if (self.player_total >= 11 and card_type == 'ace'): #If the player is at 11 points and the card is an ace, the ace becomes a value of 1
#				card_value = 1 
			self.player_total += card_value
		else: 
#			if (self.dealer_total >= 11 and card_type == 'ace'): 
#				card_value = 1
			self.dealer_total += card_value
		return (card_type, card_suit)

	def error(self, chan, msg, reason=None):
		if reason:
			self.sendmsg(chan, '[{0}] {1} {2}'.format(color('ERROR', red), msg, color('({0})'.format(str(reason)), grey)))
		else:
			self.sendmsg(chan, '[{0}] {1}'.format(color('ERROR', red), msg))

	def event_connect(self):
		if (self.mini_deck): self.setup_deck('mini')
		else: self.setup_deck('normal')
		if config.login.nickserv:
			self.identify(self.username, config.login.nickserv)
		if config.login.operator:
			self.oper(config.ident.username, config.login.operator)
		self.join(config.connection.channel, config.connection.key)

	def event_disconnect(self):
		self.sock.close()
		self.reset()
		time.sleep(10)
		self.connect()

	def event_kick(self, nick, chan, kicked):
		if kicked == config.ident.nickname and chan == config.connection.channel:
			time.sleep(3)
			self.join(config.connection.channel, config.connection.key)

	def event_message(self, nick, chan, msg):
		if chan == config.connection.channel:
			if not msg.startswith(config.settings.cmd_char):
				if msg == '@help':
					self.action(chan, 'Sending help in a private message...')
					help = [line.strip() for line in open(help_file).readlines() if line]
					for line in help:
						self.sendmsg(nick, line)
				elif msg == '@cheat':
					self.action(chan, 'Sending cheat sheet in a private message...')
					cheat_sheet = [line.strip() for line in open(cheat_file).readlines() if line]
					for line in cheat_sheet:
						self.sendmsg(nick, line)
			else:
				cmd  = msg.split()[0][1:]
				args = msg[len(cmd)+2:]
#				if time.time() - self.last_time < 2:
#					self.sendmsg(chan, color('Slow down nerd!', red))
				if cmd == 'hit':
					if self.player:
						if self.player == nick:
							card_type, card_suit = self.draw()
							if self.mini_deck:
								msg_str = ''
								for i in self.player_hand:
									msg_str += ' ' + i
								self.sendmsg(chan, msg_str)
							else:
								for i in range(5):
									msg_str = ''
									for i in self.player_hand[i]:
										msg_str += ' ' + i
									self.sendmsg(chan, msg_str)
							if self.player_total > 21:
								num_aces = 0
								for i in self.player_hand:
									if ("A" in i): #Check if there is an ace in the player's hand
										num_aces = num_aces + 1
								if (num_aces > self.player_ace_minus):
									self.player_total = self.player_total - 10
									self.player_ace_minus = self.player_ace_minus + 1
								if self.player_total > 21: #Check if it's still over 21, even after adjusting using aces
									self.sendmsg(chan, '{0} {1}'.format(color('BUST!', red), color('You went over 21 and lost!', grey)))
									self.reset()
								else:
									self.sendmsg(chan, '{0} {1} {2}'.format(color('You drew a {0} of {1}! Your total is now:'.format(card_type, card_suit[1]), yellow),  color(str(self.player_total), light_blue), color('.hit or .stand', yellow)))
									self.last_move = time.time()
								#else:
								#	self.sendmsg(chan, '{0} {1}'.format(color('BUST!', red), color('You went over 21 and lost!', grey)))
								#	self.reset()
							else:
								self.sendmsg(chan, '{0} {1} {2}'.format(color('You drew a {0} of {1}! Your total is now:'.format(card_type, card_suit[1]), yellow),  color(str(self.player_total), light_blue), color('.hit or .stand', yellow)))
								self.last_move = time.time()
						else:
							self.error(chan, 'You are not currently playing!', '{0} is playing still'.format(self.player))
					else:
						self.error(chan, 'You are not currently playing!')
#				elif cmd == 'mini':
#					if not self.player:
#						if self.mini_deck:
#							self.setup_deck('normal')
#							self.sendmsg(chan, '{0} {1}'.format(color('Mini deck has been', yellow), color('DISABLED', red)))
#						else:
#							self.setup_deck('mini')
#							self.sendmsg(chan, '{0} {1}'.format(color('Mini deck has been', yellow), color('ENABLED', green)))
#					else:
#						self.error(chan, 'You can not change the deck in game!')
				elif cmd == 'play' or cmd == 'deal':
					if not self.player:
						self.player = nick
						self.action(chan, 'Starting a game of blackjack with {0}!'.format(nick))
						for i in range(2):
							self.draw()
							self.draw(dealer=True)
						if self.mini_deck:
							msg_str = 'Your Hand'
							for i in self.player_hand:
								msg_str += ' ' + i
							self.sendmsg(chan, msg_str)
							msg_str = 'Dealer Hand'
							msg_str += ' ' + self.dealer_hand[0] #Only show first card since it's the dealer
							self.sendmsg(chan, msg_str)
						else:
							for i in range(5):
								msg_str = 'Player Hand'
								for i in self.player_hand[i]:
									msg_str += ' ' + i
								self.sendmsg(chan, msg_str)
								msg_str = 'Dealer Hand'
								msg_str += ' ' + str(self.dealer_hand[i][0]) #Only show first card since it's the dealer
								self.sendmsg(chan, msg_str)
						self.sendmsg(chan, '{0} {1} {2}'.format(color('Your total is now:', yellow), color(str(self.player_total), light_blue), color('.hit or .stand', yellow)))						
						self.last_move = time.time()
						threading.Thread(target=self.timer).start()
					elif self.player == nick:
						self.error(chan, 'You have already started a game, please finish or stop the game!'.format(self.player))
					else:
						self.error(chan, '{0} is currently playing a game, please wait!'.format(self.player))
				elif cmd == 'stand' or cmd == 'stay':
					if self.player:
						if self.player == nick:
							self.sendmsg(chan, 'You have chosen to stand with {0} as your total.'.format(color(self.player_total, light_blue)))
							self.dealer_play(chan)
							
						else:
							self.error(chan, 'You are not currently playing!', '{0} is playing still'.format(self.player))
					else:
						self.error(chan, 'You are not currently playing!')
				elif cmd == 'stop':
					if self.player:
						if self.player == nick:
							self.action(chan, 'Ending current game with {0}!'.format(nick))
							self.reset()
						else:
							self.error(chan, 'You are not currently playing!', '{0} is playing still'.format(self.player))
					else:
						self.error(chan, 'You are not currently playing!')
			self.last_time = time.time()

	def dealer_play(self, chan):
		msg_str = 'Dealer Hand'
		for i in self.dealer_hand:
			msg_str += ' ' + i
		self.sendmsg(chan, msg_str)
		done = False
		winner = ""
		while (not done):
			time.sleep(1)
			self.last_move = time.time()

			if self.dealer_total > 21:
				num_aces = 0
				for i in self.dealer_hand:
					if ("A" in i): #Check if there is an ace in the player's hand
						num_aces = num_aces + 1
				if (num_aces > self.dealer_ace_minus):
					self.dealer_total = self.dealer_total - 10
					self.dealer_ace_minus = self.dealer_ace_minus + 1
				if self.dealer_total > 21: #Check if it's still over 21, even after adjusting using aces
					self.sendmsg(chan, '{0} {1}'.format(color('DEALER BUSTS!', green), color('Dealer went over 21 and lost!', grey)))
					winner = "Player"
					done = True
					break
				else:
					self.sendmsg(chan, '{0} {1}'.format(color('Dealer total is now:', yellow), color(str(self.dealer_total), light_blue)))

			if (self.dealer_total) == 21: 
				self.sendmsg(chan, 'The dealer chosen to stand with {0} as its total.'.format(color(self.dealer_total, light_blue)))
				winner = "Dealer"
				done = True

			elif (self.dealer_total >= 17): #Dealer always stands at or over 17 if it's at 21 or under
				self.sendmsg(chan, 'The dealer chosen to stand with {0} as its total.'.format(color(self.dealer_total, light_blue)))
				if (self.dealer_total >= self.player_total):
					winner = "Dealer"
					done = True
				else:
					winner = "Player"
					done = True

			elif self.player_total <= self.dealer_total: 
				self.sendmsg(chan, 'The dealer chosen to stand with {0} as its total.'.format(color(self.dealer_total, light_blue)))
				winner = "Dealer"
				done = True

			elif self.player_total > self.dealer_total: #Dealer will always hit if it's lower than player
				self.draw(dealer=True)
				msg_str = color('Dealer Hits - Dealer Hand',yellow)
				for i in self.dealer_hand:
					msg_str += ' ' + i
				self.sendmsg(chan, msg_str)
				if (not self.dealer_total > 21): 
					self.sendmsg(chan, '{0} {1}'.format(color('Dealer total is now:', yellow), color(str(self.dealer_total), light_blue)))
		
		if (winner != "Dealer"):
			self.sendmsg(chan, '{0} {1} | {2} {3}'.format(color('Game Finished - ' + self.player + ' wins with:', green), color(str(self.player_total), light_blue), color('Dealer with:', red), color(str(self.dealer_total), light_blue)))
		else:
			self.sendmsg(chan, '{0} {1} | {2} {3}'.format(color('Game Finished - Dealer wins with:', green), color(str(self.dealer_total), light_blue), color(self.player + ' with:', red), color(str(self.player_total), light_blue)))
		self.reset()

	def event_nick_in_use(self):
		debug.error_exit('BlackJack is already running.')

	def event_part(self, nick, chan):
		if self.player == nick:
			self.sendmsg(chan, 'The game with {0} has ended.'.format(color(self.nick, light_blue)))
			self.reset()

	def event_quit(self, nick):
		if self.player == nick:
			self.sendmsg(chan, 'The game with {0} has ended.'.format(color(self.nick, light_blue)))
			self.reset()

	def handle_events(self, data):
		args = data.split()
		if args[0] == 'PING':
			self.raw('PONG ' + args[1][1:])
		elif args[1] == '001': # Use 002 or 003 if you run into issues.
			self.event_connect()
		elif args[1] == '433':
			self.event_nick_in_use()
		elif args[1] in ('KICK','PART','PRIVMSG','QUIT'):
			nick  = args[0].split('!')[0][1:]
			if nick != config.ident.nickname:
				if args[1] == 'KICK':
					chan   = args[2]
					kicked = args[3]
					self.event_kick(nick, chan, kicked)
				elif args[1] == 'PART':
					chan = args[2]
					self.event_part(nick, chan)
				elif args[1] == 'PRIVMSG':
					chan = args[2]
					msg  = data.split('{0} PRIVMSG {1} :'.format(args[0], chan))[1]
					if chan != config.ident.nickname:
						self.event_message(nick, chan, msg)
				elif args[1] == 'QUIT':
					self.event_quit(nick)

	def identify(self, username, password):
		self.sendmsg('nickserv', f'identify {username} {password}')

	def join(self, chan, key=None):
		self.raw(f'JOIN {chan} {key}') if key else self.raw('JOIN ' + chan)

	def listen(self):
		while True:
			try:
				data = self.sock.recv(1024).decode('utf-8')
				if data:
					for line in (line for line in data.split('\r\n') if line):
						debug.irc(line)
						if line.startswith('ERROR :Closing Link:') and config.ident.nickname in data:
							raise Exception('Connection has closed.')
						elif len(line.split()) >= 2:
							self.handle_events(line)
				else:
					debug.error('No data recieved from server.')
					break
			except (UnicodeDecodeError,UnicodeEncodeError):
				debug.error('Unicode error has occured.')
			except Exception as ex:
				debug.error('Unexpected error occured.', ex)
				break
		self.event_disconnect()

	def mode(self, target, mode):
		self.raw(f'MODE {target} {mode}')

	def raw(self, msg):
		self.sock.send(bytes(msg + '\r\n', 'utf-8'))

	def reset(self):
		self.ace       = [False,False]
		self.last_move = 0
		self.player    = None
		self.player_total     = 0
		self.dealer_total	= 0
		self.player_ace_minus = 0
		self.dealer_ace_minus = 0
		if self.mini_deck:
			self.player_hand = []
			self.dealer_hand = []
		else:
			self.player_hand = {0:[],1:[],2:[],3:[],4:[]}
			self.dealer_hand = {0:[],1:[],2:[],3:[],4:[]}
		deck['ace'][1] = 11
		for card in deck:
			deck[card][2] = [club,diamond,heart,spade]

	def sendmsg(self, target, msg):
		time.sleep(1)
		self.raw(f'PRIVMSG {target} :{msg}')

	def setup_deck(self, deck_type):
		if deck_type == 'mini':
			self.player_hand = []
			self.dealer_hand = []
			self.mini_deck   = True
			deck['ace'][0]   = 'A X'
			deck['two'][0]   = '2 X'
			deck['three'][0] = '3 X'
			deck['four'][0]  = '4 X'
			deck['five'][0]  = '5 X'
			deck['six'][0]   = '6 X'
			deck['seven'][0] = '7 X'
			deck['eight'][0] = '8 X'
			deck['nine'][0]  = '9 X'
			deck['ten'][0]   = '10X'
			deck['jack'][0]  = 'J X'
			deck['queen'][0] = 'Q X'
			deck['king'][0]  = 'K X'
		elif deck_type == 'normal':
			self.player_hand = {0:[],1:[],2:[],3:[],4:[]}
			self.dealer_hand = {0:[],1:[],2:[],3:[],4:[]}
			self.mini_deck   = False
			deck['ace'][0]   = ('A      ','       ','   X   ','       ','      A')
			deck['two'][0]   = ('2      ','   X   ','       ','   X   ','      2')
			deck['three'][0] = ('3      ','   X   ','   X   ','   X   ','      3')
			deck['four'][0]  = ('4      ','  X X  ','       ','  X X  ','      4')
			deck['five'][0]  = ('5      ','  X X  ','   X   ','  X X  ','      5')
			deck['six'][0]   = ('6      ','  X X  ','  X X  ','  X X  ','      6')
			deck['seven'][0] = ('7      ','  X X  ','  XXX  ','  X X  ','      7')
			deck['eight'][0] = ('8      ','  XXX  ','  X X  ','  XXX  ','      8')
			deck['nine'][0]  = ('9      ','  XXX  ','  XXX  ','  XXX  ','      9')
			deck['ten'][0]   = ('10     ','  XXX  ',' XX XX ','  XXX  ','     10')
			deck['jack'][0]  = ('J      ','       ','   X   ','       ','      J')
			deck['queen'][0] = ('Q      ','       ','   X   ','       ','      Q')
			deck['king'][0]  = ('K      ','       ','   X   ','       ','      K')

	def timer(self):
		while self.player:
			if time.time() - self.last_move > config.settings.timeout:
				self.sendmsg(config.connection.channel, '{0}, you took too long! The game has ended.'.format(self.player))
				self.reset()
				break
			else:
				time.sleep(1)

BlackJack = IRC()
