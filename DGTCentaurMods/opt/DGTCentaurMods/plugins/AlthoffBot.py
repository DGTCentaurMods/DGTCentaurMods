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

import chess, re, random

from DGTCentaurMods.classes import Log
from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts

from typing import Optional


_GAME_MODES = [_BLUNDER, _NORMAL, _EXPERT] = range(0,3)
_CAPTIONS = ["Blunder mode", "Normal mode", "Expert mode"]

# CT800 is a FLOSS dedicated chess computer designed by Rasmus Althoff.
# This plugin uses the CT800 with an adaptative mode that updates the level engine
# depending of the position evaluation.
class AlthoffBot(Plugin):

    _mode = _NORMAL
    _elo = None

    # This function is automatically invoked when
    # the user launches the plugin.
    def start(self):
        super().start()

        Centaur.set_chess_engine("ct800")

        self._adjust_chess_engine(1800)

    # This function is automatically invoked each
    # time the player pushes a key.
    # Except the BACK key which is handled by the engine.
    def key_callback(self, key:Enums.Btn):

        # If the user pushes HELP,
        # we display an hint using Stockfish engine.
        if key == Enums.Btn.HELP:
            Centaur.hint()

            # Key has been handled.
            return True
        
        # Key can be handled by the engine.
        return False
        
    # When exists, this function is automatically invoked
    # when the game engine state is affected.
    def event_callback(self, event:Enums.Event, outcome:Optional[chess.Outcome]):

        # If the user chooses to leave,
        # we quit the plugin.
        if event == Enums.Event.QUIT:
            self.stop()

        # End game
        if event == Enums.Event.TERMINATION:

            if outcome.winner == self.HUMAN_COLOR:
                Centaur.sound(Enums.Sound.VICTORY)
            else:
                Centaur.sound(Enums.Sound.GAME_LOST)

        # Player must physically play a move.
        if event == Enums.Event.PLAY:

            turn = self.chessboard.turn

            current_player = "You" if turn == chess.WHITE else "Althoff bot"

            # We display the board header.
            Centaur.header(
                text=f"{current_player} {'W' if turn == chess.WHITE else 'B'}",
                web_text=f"turn -> {current_player} {'(WHITE)' if turn == chess.WHITE else '(BLACK)'}")

            # Computer turn?
            if turn == (not self.HUMAN_COLOR):

                # On blunder mode, if ELO<1300,
                # computer can blunder if captures
                # are available...
                if self._mode == _BLUNDER and self._elo <1300:

                    # We get all the legal moves.
                    legal_moves = list({
                        "move":str(move),
                        "source":self.chessboard.piece_type_at(chess.parse_square(str(move)[0:2])),
                        "target":self.chessboard.piece_type_at(chess.parse_square(str(move)[2:4])),
                
                    } for move in list(self.chessboard.legal_moves))

                    # We get all the moves that capture a piece but pawns.
                    capture_moves = list(filter(lambda m:m["target"] and m["target"] != chess.PAWN, legal_moves))

                    # Capture blunders found?
                    if len(capture_moves):

                        Log.debug(f"Capture blunder mode activated.")

                        Centaur.play_computer_move(
                            random.choice(capture_moves)["move"]
                        )
                        return
                    else:

                        # We get all the pawn moves.
                        pawn_moves = list(filter(lambda m:m["source"] == chess.PAWN, legal_moves))

                        # Capture blunders found?
                        if len(pawn_moves):

                            Log.debug(f"Pawn move blunder mode activated.")

                            Centaur.play_computer_move(
                                random.choice(pawn_moves)["move"]
                            )
                            return


                def engine_callback(result):
                    if result:
                        Centaur.play_computer_move(str(result.move))

                        # Position needs to be evaluated again.
                        self._evaluate_position_and_adjust_level()

                # Computer is going to play asynchronously.
                # (in the meantime, user can takeback or force a move...)
                Centaur.request_chess_engine_move(engine_callback)

    # When exists, this function is automatically invoked
    # when the player takes back a move.
    def undo_callback(self, uci_move:str, san_move:str, field_index:chess.Square):
        
        # Position needs to be evaluated again.
        self._evaluate_position_and_adjust_level()
    
    # When exists, this function is automatically invoked
    # when the player physically plays a move.
    def move_callback(self, uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square):
        
        if color == self.HUMAN_COLOR:
            # Position needs to be evaluated again.
            self._evaluate_position_and_adjust_level()

        # Move is always accepted.
        return True

     # When exists, this function is automatically invoked
     # at start, after splash screen, on PLAY button.
    def on_start_callback(self, key:Enums.Btn) -> bool:

        if key == Enums.Btn.UP:
            self.HUMAN_COLOR = chess.WHITE

        elif key == Enums.Btn.DOWN:
            self.HUMAN_COLOR = chess.BLACK
            # If computer is white, we reverse the screen.
            Centaur.reverse_board()

        elif key == Enums.Btn.TICK:
            Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            self._mode += 1
            if self._mode == len(_GAME_MODES):
                self._mode = 0

            Centaur.print(_CAPTIONS[self._mode], row=11.5)

            # We do not start the game yet.
            return False

        else:
            # User must choose a color.
            return False

        # Start a new game.
        Centaur.start_game(
            white="You", 
            black="Althoff bot", 
            event="Bots chess event 2024",
            flags=Enums.BoardOption.CAN_UNDO_MOVES | Enums.BoardOption.CAN_FORCE_MOVES)
        
        # Game started.
        return True

     # When exists, this function is automatically invoked
     # when the plugin starts.
    def splash_screen(self) -> bool:

        Centaur.clear_screen()

        Centaur.print("ALTHOFF", font=fonts.SMALL_DIGITAL_FONT, row=2)
        Centaur.print("BOT", font=fonts.SMALL_DIGITAL_FONT, row=4)
        Centaur.print("Adaptative", font=fonts.SMALL_FONT, row=5.5)
        Centaur.print("CT800 bot", font=fonts.SMALL_FONT)

        Centaur.print_button_label(Enums.Btn.UP, row=8, x=6, text="Play white")
        Centaur.print_button_label(Enums.Btn.DOWN, row=9, x=6, text="Play black")
        Centaur.print_button_label(Enums.Btn.TICK, row=10.5, x=54)

        Centaur.print(_CAPTIONS[self._mode], row=11.5)

        Centaur.print_button_label(Enums.Btn.BACK, row=13.5, x=6, text="Back home")

        # The splash screen is activated.
        return True

    # Adjust the chess engine level.
    def _adjust_chess_engine(self, elo:int):

        # On expert mode, ELO can not be under 1500.
        if self._mode == _EXPERT and elo<1600:
            return

        if self._elo != elo:
            Centaur.configure_chess_engine({"UCI_Elo": elo})
            Log.debug(f"Chess engine ELO adjusted from {self._elo} to {elo}.")
            self._elo = elo
        else:
            Log.debug(f"Chess engine ELO is {self._elo}.")

    # Evaluate and adjust the chess engine level.
    def _evaluate_position_and_adjust_level(self):
        
        def engine_callback(result):
            if result and "score" in result:

                str_score = str(result["score"])

                Log.debug(str_score)

                if "Mate" in str_score:

                    # Player wins.
                    if "WHITE" in str_score and self.HUMAN_COLOR:
                        self._adjust_chess_engine(2400)
                    else:
                        self._adjust_chess_engine(1000)
                    
                else:

                    # We capture the evaluation.
                    # PovScore(Cp(-229), WHITE)
                    value = int(re.search(r'PovScore\(Cp\(([-+]\d+)\)', str_score)[1])

                    # We set the evaluation range from -100 to +100.
                    if value>+100:
                        value=+100
                    if value<-100:
                        value=-100

                    # We set WHITE point of view.
                    if "BLACK" in str_score:
                        value = value * -1

                    # We reverse the evaluation if player is BLACK
                    if self.HUMAN_COLOR == chess.BLACK:
                        value = value * -1

                    if abs(value)<3:
                        Log.debug(f"Position is equal.")
                    else:
                        Log.debug(f"Player LOSES ({value})." if value<0 else f"Player WINS (+{value}).")

                    # Engine level range is 1000-2400 with 14 distinct values.
                    new_elo = 1000+(int(((value+100)/200)*14)*100)

                    self._adjust_chess_engine(new_elo)

        # We ask for a new position evaluation.
        Centaur.request_chess_engine_evaluation(engine_callback)