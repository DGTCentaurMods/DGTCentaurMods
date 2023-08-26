# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.game.classes import Log, GameFactory, CentaurScreen, CentaurBoard
from DGTCentaurMods.game.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.game.consts import Enums, fonts

import time, chess, berserk, threading

exit_requested = False
stream_game_state = None

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

def main():

    global exit_requested
    global stream_game_state

    exit_requested = False

    w = SCREEN.write_text

    def _missing_token_screen():
        SCREEN.clear_area()
        w(2, "Please set")
        w(3, "a valid token")
        w(4, "using the web")
        w(5, "interface or")
        w(6, "editing the")
        w(7, '"centaur.ini"')
        w(8, "config file!")

    def _incorrect_token_screen():
        SCREEN.clear_area()
        w(2, "SORRY :(")
        w(3, "")
        w(4, "Unable to")
        w(5, "connect to")
        w(6, "Lichess using")
        w(7, "your token!")
    
    def _welcome_screen():
        SCREEN.clear_area()
        w(2, "WELCOME")
        w(3, f"{current_game['username'] }!")
        w(4, "")
        w(5, "Please create")
        w(6, "a game from")
        w(7, "the Lichess")
        w(8, "web interface!")

    def _key_callback(key_index):
        global exit_requested

        if key_index == Enums.Btn.BACK:
            CENTAUR_BOARD.unsubscribe_events()
            exit_requested = True

    CENTAUR_BOARD.subscribe_events(_key_callback, None)

    current_game = {"username":None, "last_board_move":None, "id":None, "color":None, "opponent": None, "your_turn": None}

    lichess_token = CentaurConfig.get_lichess_settings("token")

    if lichess_token == None or len(lichess_token) == 0:

        _missing_token_screen()
        lichess_token = None

    if lichess_token != None:

        lichess_session = berserk.TokenSession(lichess_token)
        lichess_client = berserk.Client(lichess_session)

        Log.info(f"Lichess token:'{lichess_token}'")

        try:
            current_game["username"] = lichess_client.account.get()["username"]
        except Exception as e:

            Log.exception(main, e)

            _incorrect_token_screen()
            lichess_token = None

            pass

        if lichess_token != None:

            _welcome_screen()

            # Waiting for new standard game
            for event in lichess_client.board.stream_incoming_events():
                """
                {
                    "type": "challenge",
                    "challenge": {
                        "id": "GAME_ID",
                        "url": "https://lichess.org/GAME_ID",
                        "status": "created",
                        "challenger": {
                            "id": "jack_bauer",
                            "name": "Jack_Bauer",
                            "title": None,
                            "rating": 1498,
                            "online": True,
                            "lag": 4,
                        },
                        "destUser": {
                            "id": "maia1",
                            "name": "maia1",
                            "title": "BOT",
                            "rating": 1493,
                            "online": True,
                        },
                        "variant": {"key": "standard", "name": "Standard", "short": "Std"},
                        "rated": False,
                        "speed": "rapid",
                        "timeControl": {"type": "clock", "limit": 600, "increment": 5, "show": "10+5"},
                        "color": "white",
                        "finalColor": "white",
                        "perf": {"icon": "\ue017", "name": "Rapid"},
                    },
                    "compat": {"bot": False, "board": True},
                }
                {
                    "type": "gameStart",
                    "game": {
                        "fullId": "GAME_ID_EX",
                        "gameId": "GAME_ID",
                        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                        "color": "white",
                        "lastMove": "",
                        "source": "friend",
                        "status": {"id": 20, "name": "started"},
                        "variant": {"key": "standard", "name": "Standard"},
                        "speed": "rapid",
                        "perf": "rapid",
                        "rated": False,
                        "hasMoved": False,
                        "opponent": {"id": "maia1", "username": "BOT maia1", "rating": 1493},
                        "isMyTurn": True,
                        "secondsLeft": 600,
                        "compat": {"bot": False, "board": True},
                        "id": "GAME_ID",
                    },
                }

                """

                #print(event)

                if 'type' in event.keys():
                    if event.get('type') == "gameStart":
                        if 'game' in event.keys():

                            game_node = event.get('game')

                            if 'variant' in game_node.keys() and game_node.get('variant').get('key') == "standard":
                                current_game["id"]  = game_node.get('id')
                                current_game["color"]  = chess.WHITE if game_node.get('color') == "white" else chess.BLACK 
                                current_game["opponent"] = game_node.get('opponent').get('username')
                                break

            def key_callback(args):

                assert "key" in args, "key_callback args needs to contain the 'key' entry!"

                key = args["key"]

                # Key has not been handled, Factory will handle it!
                return False


            def event_callback(args):

                assert "event" in args, "event_callback args needs to contain the 'event' entry!"

                global exit_requested
                global stream_game_state

                if args["event"] == Enums.Event.QUIT:

                    exit_requested = True
                    del stream_game_state

                if args["event"] == Enums.Event.PLAY:

                    current_game["your_turn"] = gfe.get_board().turn == current_game["color"]

                    current_player = current_game["username"] if current_game["your_turn"] else current_game["opponent"]

                    SCREEN.write_text(1,f"{current_player} {'W' if gfe.get_board().turn == chess.WHITE else 'B'}", font=fonts.FONT_Typewriter_small, bordered=True, centered=True)

                    gfe.send_to_web_clients({ 
                        "turn_caption":f"turn → {current_player} ({'WHITE' if gfe.get_board().turn == chess.WHITE else 'BLACK'})"
                    })

            
            def move_callback(args):

                # field_index, san_move, uci_move are available
                assert "uci_move" in args, "args needs to contain 'uci_move' key!"
                assert "san_move" in args, "args needs to contain 'san_move' key!"
                assert "field_index" in args, "args needs to contain 'field_index' key!"

                current_game["last_board_move"] = None

                if current_game["your_turn"]:
                    
                    Log.info(f'Sending move of "{current_game["username"]}".')

                    current_game["last_board_move"] = args["uci_move"]
                    
                    lichess_client.board.make_move(current_game["id"], args["uci_move"])

                    return True

                # Move is accepted only if we receive a move from Lichess
                # From GameFactory perspective,
                # Computer move == Lichess opponent move
                return gfe.computer_move_available()

            # Subscribe to the game factory
            gfe = GameFactory.Engine(
                
                event_callback = event_callback,
                move_callback = move_callback,
                key_callback = key_callback,

                flags = Enums.BoardOption.EVALUATION_DISABLED | Enums.BoardOption.DB_RECORD_DISABLED,

                game_informations = {
                    "event" : "Lichess",
                    "site"  : "",
                    "round" : "",
                    "white" : current_game["opponent"] if current_game["color"] == chess.BLACK else current_game["username"] ,
                    "black" : current_game["opponent"] if current_game["opponent"] == chess.WHITE else current_game["username"] ,
                })

            # Game stream
            stream_game_state = lichess_client.board.stream_game_state(current_game["id"])
            
            # The game starts or is being resumed
            while True:

                try:
                    state = next(stream_game_state)
                except:
                    state = None
                    pass

                if exit_requested:
                    break

                if state:
                    #print(state)
                    """
                    {
                        "type": "gameState",
                        "moves": "e2e4",
                        "wtime": datetime.datetime(1970, 1, 1, 0, 10, tzinfo=datetime.timezone.utc),
                        "btime": datetime.datetime(1970, 1, 1, 0, 10, tzinfo=datetime.timezone.utc),
                        "winc": datetime.datetime(1970, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc),
                        "binc": datetime.datetime(1970, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc),
                        "status": "started",
                    }
                    {
                        "type": "chatLine",
                        "room": "player",
                        "username": "maia1",
                        "text": "Hi Jack Bauer, I'm currently taking my time like a human. If you type 'go' or 'fast' in the chat I'll play faster. gl hf",
                    }
                    {
                        "type": "gameState",
                        "moves": "e2e4 e7e5 b1c3 g8f6 f2f4 e5f4 e4e5 f6g8 g1f3 d7d6 d2d4 d6e5 f3e5 f8d6 c1f4 d6e5 f4e5 f7f6 e5g3 d8e7 d1e2 e7e2 f1e2 b8c6 e1c1 g8e7 h1e1 e8g8 e2c4 g8h8 g3c7 c8g4 d1d2 a8c8 c7d6 f8e8 d4d5 c6a5 c4b5 e8d8 d6e7 d8e8 b5e8 c8e8 d5d6 a5c4 d2d4 c4e5 h2h3 g4h5 e1e5 f6e5 d4d5 h5f7 d5e5 h7h6 e5f5 f7e6 f5f8 e8f8 e7f8 h8g8 f8e7 g8f7 a2a3 f7e8 b2b4 e8d7 c1d2 g7g5 d2e3 h6h5 c3a4 g5g4 a4c5 d7c6 c5e6 g4h3 g2h3 h5h4 c2c4 c6d7 e6c5 d7c6 d6d7 c6c7 d7d8q c7c6 d8d7 c6b6 d7b7",
                        "wtime": datetime.datetime(
                            1970, 1, 1, 0, 5, 17, 950000, tzinfo=datetime.timezone.utc
                        ),
                        "btime": datetime.datetime(
                            1970, 1, 1, 0, 9, 8, 370000, tzinfo=datetime.timezone.utc
                        ),
                        "winc": datetime.datetime(1970, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc),
                        "binc": datetime.datetime(1970, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc),
                        "status": "mate",
                        "winner": "white",
                    }
                    """
                    
                    if gfe.is_started() == False:

                        if 'state' in state.keys():

                            # Game is being resumed...
                            uci_moves = state.get('state').get('moves').split()

                            gfe.start(uci_moves)

                    if 'wdraw' in state.keys() or 'bdraw' in state.keys():
                        # TODO handle draw proposal
                        lichess_client.board.decline_draw(current_game["id"])
                        pass

                    else:
                        if 'type' in state.keys() and state.get('type') == "gameState" and 'moves' in state.keys():
                            
                            # We take the last move of the list
                            uci_move = state.get('moves').split()[-1]

                            if uci_move == current_game["last_board_move"]:
                                Log.info(f'Last board move "{uci_move}" validated by Lichess.')

                            else:
                                Log.info(f'Player "{current_game["opponent"]}" played "{uci_move}".')

                                gfe.set_computer_move(uci_move)

                            if 'status' in state.keys() and state.get('status') != "started":
                                # Might be mate...
                                gfe.update_evaluation(force=True, text=state.get('status'))
                                pass

    while exit_requested == False:
        time.sleep(0.1)

if __name__ == '__main__':
    main()