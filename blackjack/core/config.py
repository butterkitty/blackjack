#!/usr/bin/env python
# BlackJack IRC Bot - Developed by butterkitty in Python, based on acidvegas' bot (https://acid.vegas/blackjack)
# config.py

class connection:
	server     = 'irc.libera.chat'
	port       = 6697
	proxy      = None
	ipv6       = False
	ssl	       = True
	ssl_verify = True
	vhost      = None
	channel	   = '#***REMOVED***'
	key	       = None

class cert:
	file     = None
	key      = None
	password = None

class ident:
	nickname = 'blackJack'
	username = 'blackjack'
	realname = None

class login:
	network  = None
	nickserv = '***REMOVED***'
	operator = None

class settings:
	cmd_char = '.'
	log      = False
	modes    = None
	mini_deck = True
	timeout	= 30
