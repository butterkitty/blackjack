![](screens/banner.png)

###### Install

docker run -v </config/path>:/blackjack/core/ \
    -e TERM=xterm \
    --name=blackjack-irc \
    --restart unless-stopped \
    -d blackjack-irc


###### Commands
| Command | Description |
| --- | --- |
| @help | Information about the commands. |
| @cheat | Betting cheat sheet. |
| .hit | Draw a card. |
| .mini | Toggle the mini deck. |
| .play | Start a game. |
| .stand | Stop drawing cards. |
| .stop | End the curent game. |

##### Todo
- Add player database / chip system.
- Reward chips based on number of lines of chat in a channel. (Cap it to prevent flood.)
- Add a player versus player and a player versus computer system.
- Incorperate splits and double downs, etc.

##### Screens
![](screens/game.png)
![](screens/cheat.png)