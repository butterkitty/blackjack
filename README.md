![](screens/banner.png)

# Install

docker run -v </config/path>:/blackjack/core/ \
    -e TERM=xterm \
    --name=blackjack-irc \
    --restart unless-stopped \
    -d butterkitty/blackjack-irc

### config.py (place in config path)
```
#!/usr/bin/env python
# BlackJack IRC Bot - Developed by butterkitty in Python, based on acidvegas' bot (https://acid.vegas/blackjack)
# config.py

class connection:
        server     = 'irc.libera.chat'
        port       = 6697
        proxy      = None
        ipv6       = False
        ssl            = True
        ssl_verify = True
        vhost      = None
        channel    = '#***REMOVED***'
        key            = None

class cert:
        file     = None
        key      = None
        password = None

class ident:
        nickname = '***REMOVED***'
        username = '***REMOVED***'
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
        timeout = 30
```
## Commands
| Command | Description |
| --- | --- |
| @help | Information about the commands. |
| @cheat | Betting cheat sheet. |
| .hit | Draw a card. |
| .mini | Toggle the mini deck. |
| .play | Start a game. |
| .stand | Stop drawing cards. |
| .stop | End the curent game. |

### Todo
- Add player database / chip system.
- Reward chips based on number of lines of chat in a channel. (Cap it to prevent flood.)
- Add a player versus player and a player versus computer system.
- Incorperate splits and double downs, etc.

### Screens
![](screens/game.png)
![](screens/cheat.png)