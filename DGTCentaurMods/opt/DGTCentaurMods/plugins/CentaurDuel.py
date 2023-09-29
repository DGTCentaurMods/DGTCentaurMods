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

import chess, time, random

from DGTCentaurMods.classes import Log
from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts, consts

from typing import Optional

# Local constants.
(SPECIFIC_DUEL_REQUEST, DUEL_REQUEST, DUEL_ACK, DUEL_MOVE, DUEL_MOVE_ACK, DUEL_ABORTED) = range(0,6)
(INITIALIZING, MASTER, SLAVE, RUNNING, PENDING_MOVE_ACK) = range(0,5) 

# Shortcuts.
print = Centaur.print
button = Centaur.print_button_label

# We pick the Lichess username when exists.
USERNAME = Centaur.configuration().get_lichess_settings("username") or "anonymous"

# Max rety when no move acknowledgement.
MAX_ACK_RETRIES = 5

# Move acknowledgement class.
class _MoveAck():

    def __init__(self) -> None:
        self.update("?","?",chess.WHITE)

    def update(self, uci_move:str, san_move:str, color:chess.Color):

        self._uci_move = uci_move
        self._san_move = san_move
        self._color = color
        self._time = time.time()
        self._tries = 0

    def __str__(self) -> str:
        return f'move "{self._uci_move}/{self._san_move}"'
    
    # Every 5 seconds we can retry to send the move.
    def is_outdated(self) -> bool:
        result = time.time() - self._time > 5
        if result:
            self._time = time.time()
        return result
    
    def check(self, uci_move) -> bool:
        return uci_move == self._uci_move
    
    def retry(self):
        self._tries += 1
        if self._tries > MAX_ACK_RETRIES:
            raise Exception(f'Tried {MAX_ACK_RETRIES} times to send the move "{self._san_move}" to the opponent but received no ACK!')
        
        Log.debug(f'Retry #{self._tries} : resending your move "{self._uci_move}/{self._san_move}"...')
        Centaur.send_external_request({ "type":DUEL_MOVE, "color":self._color, "san_move":self._san_move, "uci_move":self._uci_move })

# Main plugin
class CentaurDuel(Plugin):

    _mode = INITIALIZING
    _opponent_username = "Anonymous"
    _expected_ack = _MoveAck()

    # This function is automatically invoked each
    # time the player pushes a key.
    # Except the BACK key which is handled by the engine.
    def key_callback(self, key:Enums.Btn):
        
        # Key can be handled by the engine.
        return False
        
    # When exists, this function is automatically invoked
    # when the game engine state is affected.
    def event_callback(self, event:Enums.Event, outcome:Optional[chess.Outcome]):

        # If the user chooses to leave,
        # we quit the plugin.
        if event == Enums.Event.QUIT:
            # We send a notification to the opponent.
            Centaur.send_external_request({ "type":DUEL_ABORTED, "username":USERNAME })
            self.stop()

        # End game.
        if event == Enums.Event.TERMINATION:

            if outcome.winner == self.YOUR_COLOR:
                Centaur.sound(Enums.Sound.VICTORY)
                Centaur.messagebox(("YOU","WIN!",None))
            else:
                Centaur.sound(Enums.Sound.GAME_LOST)
                Centaur.messagebox(("YOU","LOOSE!",None))

        # Player must physically play a move.
        if event == Enums.Event.PLAY:

            turn = self.chessboard.turn

            current_player = "You" if turn == self.YOUR_COLOR else self._opponent_username

            # We display the board header.
            Centaur.header(
                text=f"{current_player} {'W' if turn == chess.WHITE else 'B'}",
                web_text=f"turn → {current_player} {'(WHITE)' if turn == chess.WHITE else '(BLACK)'}")
            
            # Pending for move acknowledgement?
            # TODO make that part asynchronous.
            while self._mode == PENDING_MOVE_ACK:
                if self._expected_ack.is_outdated():
                    self._expected_ack.retry()
                time.sleep(.1)


    # When exists, this function is automatically invoked
    # when the player physically plays a move.
    def move_callback(self, uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square):

        # Your move?
        if color == self.YOUR_COLOR:

            Log.debug(f'Sending your move "{uci_move}/{san_move}" to "{self._opponent_username}"...')

            Centaur.send_external_request({ "type":DUEL_MOVE, "color":color, "san_move":san_move, "uci_move":uci_move })

            # Waiting for ack.
            self._mode = PENDING_MOVE_ACK
            self._expected_ack.update(uci_move, san_move, color)

            return True

        # Move rejected if the opponent did not play.
        # (from engine perspective, opponent == computer)
        return Centaur.computer_move_is_ready()
    
    # When exists, this function is automatically invoked
    # on socket messages.
    def on_socket_request(self, data:dict):

        # External request?
        if consts.EXTERNAL_REQUEST in data:

            request = data[consts.EXTERNAL_REQUEST]
            request_type = request.get("type", None)

            # We read the CUUID of the request.
            # Who sent the request?
            OPPONENT_CUUID = request.get("cuuid", None)

            # Game running or waiting for move acknowledgement.
            if self._mode in (RUNNING, PENDING_MOVE_ACK):

                # Not your opponent...
                # We ignore the request.
                if OPPONENT_CUUID != self._opponent_cuuid:
                    return
                
                # Our opponent left the game...
                if request_type == DUEL_ABORTED:
                    Centaur.sound(Enums.Sound.COMPUTER_MOVE)
                    Centaur.messagebox((self._opponent_username,"LEFT THE","GAME!"))
                    return

                # Only move requests are valid during a game.
                if request_type not in (DUEL_MOVE, DUEL_MOVE_ACK):
                    return

                turn = self.chessboard.turn

                # We read the color of the game request.
                color = request.get("color", None)

                # Simple move.
                if request_type == DUEL_MOVE:

                    # Opponent turn?
                    # Opponent move?
                    if turn != self.YOUR_COLOR and turn == color:

                        uci_move = request.get("uci_move", None)
                        san_move = request.get("san_move", None)

                        Log.debug(f'Receiving the move "{uci_move}/{san_move}" from "{self._opponent_username}"...')

                        Centaur.play_computer_move(uci_move)

                        # We send back the move acknowledgement.
                        Centaur.send_external_request({ "type":DUEL_MOVE_ACK, "uci_move":uci_move })

                # Move acknowledgement.
                # Your opponent received your move.
                elif request_type == DUEL_MOVE_ACK:

                    # Are you waiting for a move acknowledgement?
                    if self._mode == PENDING_MOVE_ACK:

                        uci_move = request.get("uci_move", None)

                        # Is the move acknowledgement matching with yours?
                        if self._expected_ack.check(uci_move):
                            self._mode = RUNNING
                        else:
                            Log.info(f'ERROR: Received ACK "{uci_move}" / Expecting "{self._expected_ack}"!')
                    else:
                        Log.info(f'ERROR: Received ACK "{uci_move}" / Expecting none!')

            # Game not started - waiting for opponent.
            elif self._mode in (SLAVE, MASTER):

                # SPECIFIC_DUEL_REQUEST == You choose a specific color.
                # DUEL_REQUEST == You don't care about the color.

                # Only duel requests and acknowledgements are accepted there.
                if request_type not in (SPECIFIC_DUEL_REQUEST, DUEL_REQUEST, DUEL_ACK):
                    return

                # If you created a specific duel request,
                # you can accept the other pending duel requests
                # only if the color is different.
                if self._mode == MASTER and request_type == SPECIFIC_DUEL_REQUEST:
                    if request.get("color", None) != self.YOUR_COLOR:
                        return

                # We get the opponent name.
                OPPONENT:str = request.get("username", "Anonymous")

                # If we requested any duel, we accept duel requests and duel acknowledgements.
                # Then we take the color from the request.
                if self._mode == SLAVE and (request_type in (SPECIFIC_DUEL_REQUEST, DUEL_ACK)):
                    self.YOUR_COLOR = request.get("color", None)

                    if self.YOUR_COLOR == None:
                        # Unable to get the color from the specific duel request/acknowledgement.
                        # Should never happen.
                        return

                # If we requested any duel and if we receive a non specific duel request,
                # We choose a random color.
                if self._mode == SLAVE and request_type == DUEL_REQUEST:
                    self.YOUR_COLOR = random.choice([chess.WHITE, chess.BLACK])

                self._mode = RUNNING

                # We send back a duel acknowledgement.
                # (that contains the opponent color)
                if request_type != DUEL_ACK:
                    Centaur.send_external_request({ "type":DUEL_ACK, "color":not self.YOUR_COLOR, "username":USERNAME })
                
                self._opponent_username = OPPONENT
                self._opponent_cuuid = OPPONENT_CUUID

                # We can start the game.
                self._start_duel(
                    white=USERNAME if self.YOUR_COLOR else OPPONENT,
                    black=OPPONENT if self.YOUR_COLOR else USERNAME)

    # When exists, this function is automatically invoked
    # at start, after splash screen, on PLAY button.
    def on_start_callback(self, key:Enums.Btn) -> bool:

        Centaur.sound(Enums.Sound.COMPUTER_MOVE)

        if key == Enums.Btn.UP:
            self.YOUR_COLOR = chess.WHITE

            self._screen_specific_duel_request()

            self._mode = MASTER

            # We choose to play white.
            # We need a black opponent.
            Centaur.send_external_request({ "type":SPECIFIC_DUEL_REQUEST, "color":chess.BLACK, "username":USERNAME })
            return True

        elif key == Enums.Btn.DOWN:
            self.YOUR_COLOR = chess.BLACK
            # If you are black, we reverse the screen.
            Centaur.reverse_board()

            self._screen_specific_duel_request()
            
            self._mode = MASTER

            # We choose to play black.
            # We need a white opponent.
            Centaur.send_external_request({ "type":SPECIFIC_DUEL_REQUEST, "color":chess.WHITE, "username":USERNAME })
            return True

        elif key == Enums.Btn.TICK or key == key == Enums.Btn.PLAY:

            self._screen_any_duel_request()

            self._mode = SLAVE

            # We don't care about the color.
            Centaur.send_external_request({ "type":DUEL_REQUEST, "username":USERNAME })
            return True

        # User must choose a color or ask for duel.
        return False

    def _start_duel(self, white:str, black:str):
        #Centaur.set_chess_engine("stockfish")
        #Centaur.configure_chess_engine({"UCI_Elo": 2200})

        # Start a new game.
        Centaur.start_game(
            white=white, 
            black=black, 
            event="Centaur chess duels event 2024",
            flags=Enums.BoardOption.EVALUATION_DISABLED | Enums.BoardOption.RESUME_DISABLED)
    
    def _screen_header(self):
        Centaur.clear_screen()

        print("Centaur", font=fonts.PACIFICO_FONT, row=1)
        print("Duel", font=fonts.PACIFICO_FONT, row=3)
    
    def _screen_specific_duel_request(self):
        self._screen_header()
        print("You just", row=6)
        print("sent")
        print("a new")
        print("duel request!")
        print()
        print("Waiting for")
        print("opponent...")
        
        button(Enums.Btn.BACK, row=13.5, x=6, text="Back home")

    def _screen_any_duel_request(self):
        self._screen_header()
        print("You are", row=6)
        print("waiting")
        print("for a duel")
        print("request...")

        button(Enums.Btn.BACK, row=13.5, x=6, text="Back home")

    # When exists, this function is automatically invoked
    # when the plugin starts.
    def splash_screen(self) -> bool:

        self._screen_header()

        print("Send a", font=fonts.SMALL_MAIN_FONT, row=5.5)
        print("duel request", font=fonts.SMALL_MAIN_FONT, row=6.1)

        button(Enums.Btn.UP, x=6, text="Play white")
        button(Enums.Btn.DOWN, x=6, text="Play black")

        print("or", font=fonts.SMALL_MAIN_FONT, row=9.5)
        print("accept any", font=fonts.SMALL_MAIN_FONT, row=10)
        print("duel request", font=fonts.SMALL_MAIN_FONT, row=10.7)

        button(Enums.Btn.TICK, x=34, text="GO!")

        button(Enums.Btn.BACK, row=13.5, x=6, text="Back home")

        # The splash screen is activated.
        return True