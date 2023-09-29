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

from DGTCentaurMods.classes import ChessEngine, DAL, Log, SocketClient, CentaurScreen, CentaurBoard, LiveScript
from DGTCentaurMods.consts import Enums, consts, fonts, menu
from DGTCentaurMods.lib import common, sys_requests

from typing import Tuple, Optional

#from pympler import muppy, summary

from threading import Thread

import time
import chess
import chess.pgn
import sys
import inspect

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()
SOCKET = SocketClient.connect_local_server()

UNDEFINED_SQUARE: chess.Square = -1

# Isolate logic of __field_callback
class PieceHandler:

    def __init__(self, engine: 'Engine') -> None:
        # Call back into engine for side-effects
        self._engine: 'Engine' = engine

        # History of field events
        self._lift1: chess.Square = UNDEFINED_SQUARE
        self._lift2: chess.Square = UNDEFINED_SQUARE
        self._place1: chess.Square = UNDEFINED_SQUARE

        # Local to a single field event
        self._web_move: bool = False

    # Engine API

    @property
    def _can_force_moves(self) -> bool:
        """Can player override computer's choice of move?"""
        return self._engine._can_force_moves

    @property
    def _can_undo_moves(self) -> bool:
        """Can player take back moves?"""
        return self._engine._can_undo_moves

    @property
    def _chessboard(self) -> chess.Board:
        return self._engine._chessboard

    @property
    def _computer_uci_move(self) -> str:
        """Computer's choice of move, stripping off promotion suffix"""
        return self._engine._computer_uci_move[0:4]

    @property
    def _dal(self):
        return self._engine._dal

    @property
    def _turn(self) -> chess.Color:
        """Color of active party"""
        return self._chessboard.turn

    def _update_display(self) -> None:
        common.update_Centaur_FEN(self._fen())
        self._engine.display_partial_PGN()
        self._engine.display_board()

    def _fen(self) -> str:
        return self._chessboard.fen()

    # Method Object

    @property
    def _piece_color_is_consistent(self) -> bool:
        """Check piece color against current turn"""
        return self._chessboard.color_at(self._lift1) == self._turn

    def _to_square_name(self, square_index: chess.Square) -> str:
        "Numbering 0 = a1, 63 = h8"
        return common.Converters.to_square_name(square_index)

    def _move_name(self) -> str:
        "Represent current move as uci"
        return self._to_square_name(self._lift1) + \
            self._to_square_name(self._place1)

    def _undo_name(self) -> str:
        """Move that undoes the previous move"""
        if prev_move := self._engine.last_uci_move:
            return prev_move[2:4] + prev_move[0:2]
        else:
            # No previous move
            return ""

    def _wrong_move(self) -> None:
        """Alert user to illegal move attempt"""

        # Get user's attention.
        CENTAUR_BOARD.beep(Enums.Sound.WRONG_MOVE)

        # Show user what move should be corrected.
        CENTAUR_BOARD.led_from_to(self._place1, self._lift1)

        # Could be a reset request...
        self._engine._update_board_state(self._web_move)

    def _is_legal_move(self, uci_move: str) -> bool:

         # We test there the basic board move, from square to square,
         # ignoring the promotion if exists

        if self._engine._computer_move_is_ready and not self._can_force_moves:
            return uci_move[0:4] == self._computer_uci_move
        else:
            legal_board_moves = (str(move)[0:4] for move in self._chessboard.legal_moves)

            return uci_move[0:4] in legal_board_moves

    def _commit_move(self, uci_move: str, san_move: str) -> None:
        if self._dal.insert_new_game_move(uci_move, str(self._fen())):
            Log.debug(f'Move "{uci_move}/{san_move}" has been committed.')
            self._engine._computer_move_is_ready = False
            self._engine._san_move_list.append(san_move)
            
            CENTAUR_BOARD.beep(Enums.Sound.CORRECT_MOVE)

            if len(self._chessboard.checkers()) > 0:
                # Highlight both moved piece and king in check
                CENTAUR_BOARD.led_array([
                    self._place1,
                    self._chessboard.king(self._turn)
                ])
            else:
                # Highlight moved piece
                CENTAUR_BOARD.led(self._place1)

            self._update_display()
            self._engine.update_web_ui({
                "clear_board_graphic_moves": True,
                "uci_move": uci_move,
                "san_move": san_move,
                "field_index": self._place1
            })
            self._engine._check_last_move_outcome_and_switch()
        else:
            # Fatal
            Log.exception(
                self._finalize_move,
                f'Move "{uci_move}/{san_move}" HAS NOT been committed.')
            self._engine.stop()

    def _accept_move(self, uci_move: str, san_move: str) -> bool:
        # We invoke the client callback
        # If the callback returns True, the move is accepted
        accepted = Engine._Engine__invoke_callback(
            self._engine._move_callback_function,
            uci_move=uci_move,
            san_move=san_move,
            color=not self._turn, # Move has been done, we need to reverse the color
            field_index=self._place1)
        if accepted:
            self._engine.update_evaluation()
            self._commit_move(uci_move, san_move)
            return True
        else:
            # Engine can still reject moves that pass our simplified
            # legality check.  It's the final authority.
            Log.debug(f'Client rejected the move "{uci_move}/{san_move}"...')
            self._chessboard.pop()
            self._wrong_move()
            return False

    def _decide_move(
            self, player_uci_move: str, promoted_piece: str = "") -> str:

        player_move = player_uci_move + promoted_piece
        if self._engine._computer_move_is_ready:
            if self._can_force_moves and \
                    player_uci_move != self._computer_uci_move:
                # Player has overridden computer's choice of move
                self._engine._computer_uci_move = player_move
            else:
                # Adopt computer's choice of move
                player_move = self._engine._computer_uci_move
        return player_move

    def _finalize_move(
            self, player_uci_move: str, promoted_piece: str = "") -> bool:
        
        self._promotion_move = None
        
        if not self._is_legal_move(player_uci_move):
            Log.debug(f'ILLEGAL move "{player_uci_move}"')
            self._wrong_move()
            return False

        uci_move = self._decide_move(player_uci_move, promoted_piece)
        try:
            move = chess.Move.from_uci(uci_move)
            self._chessboard.push(move)
            san_move = self._engine.last_san_move
            return self._accept_move(uci_move, san_move)
        except Exception as e:
            Log.debug(f'INVALID move "{uci_move}"')
            self._wrong_move()
            return False

    def _is_promotion(self) -> bool:
        piece_name = self._chessboard.piece_at(self._lift1).symbol()

        white_pawn, black_pawn = piece_name == "P", piece_name == "p"

        rank = self._place1 // 8

        first_rank, last_rank = rank == 0, rank == 7

        return (white_pawn and last_rank) or (black_pawn and first_rank)

    def _ask_user_for_promotion(self) -> bool:
        """Promotion menu display if player is human or if player
        overrides computer move"""
        return not self._engine._computer_move_is_ready or \
            self._move_name() != self._computer_uci_move

    _PROMOTION_KEYS = {
        Enums.Btn.BACK: "n",
        Enums.Btn.TICK: "b",
        Enums.Btn.UP: "q",
        Enums.Btn.DOWN: "r",
    }

    def _promote_key_callback(self, key) -> bool:
        if promoted_piece := self._PROMOTION_KEYS.get(key):
            CENTAUR_BOARD.unsubscribe_events()
            self._engine.display_board()

            return self._finalize_move(self._promotion_move, promoted_piece)

    def _prompt_for_promotion(self) -> None:

        self._promotion_move = self._move_name()

        CENTAUR_BOARD.beep(Enums.Sound.COMPUTER_MOVE)
        SCREEN.draw_promotion_window()
        CENTAUR_BOARD.subscribe_events(self._promote_key_callback)

    def _attempt_move(self) -> bool:
        """Piece has been moved"""

        Log.info(f'Piece has been moved to "{self._to_square_name(self._place1)}".')
        if self._is_promotion() and self._ask_user_for_promotion():
            self._prompt_for_promotion()
        else:
            return self._finalize_move(self._move_name())

        return True

    def _is_takeback(self) -> bool:
        """Is this an attempt to take back a move?"""
        return not self._piece_color_is_consistent and \
            self._can_undo_moves and \
            self._move_name() == self._undo_name()

    def _takeback_move(self) -> bool:
        """Previous move has been taken back"""

        previous_uci_move = self._chessboard.pop().uci()
        previous_san_move = self._engine._san_move_list.pop()
        Log.debug(f'Undoing move "{previous_uci_move}"...')

        Log.debug(f'Move "{previous_uci_move}/{previous_san_move}" will be removed from DB...')
        self._dal.delete_last_game_move()

        self._engine._computer_move_is_ready = False

        CENTAUR_BOARD.beep(Enums.Sound.TAKEBACK_MOVE)
        CENTAUR_BOARD.led(self._place1)
        self._update_display()
        self._engine.update_web_ui({
            "clear_board_graphic_moves": True,
            "uci_undo_move": self._undo_name(),
            "uci_move": self._engine.last_uci_move,
        })

        Engine._Engine__invoke_callback(
            self._engine._undo_callback_function,
            uci_move=previous_uci_move,
            san_move=previous_san_move,
            field_index=self._place1)
        
        Engine._Engine__invoke_callback(
            self._engine._event_callback_function,
            event=Enums.Event.PLAY,
            outcome=None)

        self._engine.update_evaluation()

        return True

    def _normalize_event_order(self) -> None:
        """Arrange events so that capturing piece is lifted first"""

        if self._lift2 == UNDEFINED_SQUARE:
            return

        # Is this a capture?
        if self._lift1 == self._place1:
            # Normalize so that moving piece is lifted first, as this
            # lets us keep most of the other code unchanged.
            self._lift2, self._lift1 = self._lift1, self._lift2

        # Beyond dealing with captures, we also want to ignore any
        # spurious LIFT actions. We do this by looking for a subset of
        # events that produce a valid move.
        if not self._is_legal_move(self._move_name()):
            # Normalize so that the first LIFT is the one that
            # produces a valid move.
            self._lift1, self._lift2 = self._lift2, None

    def _interpret_actions(self) -> bool:
        """Take action based on history of field events"""

        result = False

        if self._lift1 == UNDEFINED_SQUARE or self._place1 == UNDEFINED_SQUARE:
            # Move is incomplete
            return False

        self._normalize_event_order()

        if self._lift1 == self._place1:
            self._engine._update_board_state(self._web_move)

            # Piece has simply been placed back
            pass
        elif self._piece_color_is_consistent:
            result = self._attempt_move()
        elif self._is_takeback():
            result = self._takeback_move()
        else:
            self._engine._update_board_state(self._web_move)

            # A LIFT and PLACE of a piece of the wrong color, that is
            # not a takeback, is assumed to be the completion of a
            # two-part move (i.e., castling) and can be ignored.
            pass

        # Clear event history for next move.
        self._lift1 = UNDEFINED_SQUARE
        self._lift2 = UNDEFINED_SQUARE
        self._place1 = UNDEFINED_SQUARE

        return result

    # Receives field events from the board.
    # field_index 0 = a1, 63 = h8
    def __call__(self, field_index: chess.Square, field_action, web_move: bool) -> None:
        Log.debug(f"field_index:{field_index}, square_name:{self._to_square_name(field_index)}, piece_action:{field_action}")

        # We do not need to check reset if piece is lifted
        self._engine._need_starting_position_check = False

        # Used to decide error path in event of illegal move
        self._web_move = web_move

        if field_action == Enums.PieceAction.LIFT:
            self._place1 = UNDEFINED_SQUARE
            if self._lift1 != UNDEFINED_SQUARE:
                # There's no normal sequence where we would expect a
                # sequence of three or more LIFT actions without an
                # intervening PLACE.  Should this occur, we ignore
                # the oldest LIFT.
                if self._lift2 != UNDEFINED_SQUARE:
                    self._lift1 = self._lift2
                self._lift2 = field_index
            else:
                self._lift1 = field_index
        elif field_action == Enums.PieceAction.PLACE:
            
            # If the state was not OK, we check again.
            if self._engine._invalid_board_state:
                self._engine._update_board_state(self._web_move)

            if self._lift1 == UNDEFINED_SQUARE:
                # A PLACE action with no corresponding LIFT is
                # likely the restoration of a previously captured
                # piece after a takeback.  We can ignore it.
                return
            self._place1 = field_index

            # Board needs to be OK before playing.
            if not self._engine._invalid_board_state:
                return self._interpret_actions()
            else:
                CENTAUR_BOARD.beep(Enums.Sound.WRONG_MOVE)
                Log.info("The board needs to be re-arranged!")
            
            return False

        else:
            # Not expected
            return False

        return self._interpret_actions()

# Game engine
class Engine():

    _started = False

    _initialized = False
    _new_evaluation_requested = False

    _previous_move_displayed = False

    _invalid_board_state = False
    _computer_move_is_ready = False

    _chessboard = None

    _san_move_list = []

    _chess_engine: ChessEngine.ChessEngineWrapper = None

    _show_evaluation = True

    def __init__(self, 
                 event_callback = None,
                 move_callback = None,
                 undo_callback = None,
                 key_callback = None,
                 socket_callback = None,
                 
                 flags = Enums.BoardOption.CAN_DO_COFFEE,

                 chess_engine = None,
                 
                 game_informations = {}):

        LiveScript.attach_game_engine(self)

        self._chessboard = chess.Board(chess.STARTING_FEN)

        SCREEN.clear_area()

        SCREEN.write_text(3,"Please place")
        SCREEN.write_text(4,"pieces in")
        SCREEN.write_text(5,"starting")
        SCREEN.write_text(6,"position!")

        self._chess_engine = chess_engine

        self._key_callback_function = key_callback
        self._move_callback_function = move_callback
        self._undo_callback_function = undo_callback
        self._event_callback_function = event_callback
        self._socket_callback = socket_callback

        self._game_informations = game_informations

        self.source = inspect.getsourcefile(sys._getframe(1))

        self._can_force_moves = Enums.BoardOption.CAN_FORCE_MOVES in flags
        self._can_undo_moves = Enums.BoardOption.CAN_UNDO_MOVES in flags

        self._evaluation_disabled = Enums.BoardOption.EVALUATION_DISABLED in flags
        self._show_evaluation = not self._evaluation_disabled

        db_record_disabled = Enums.BoardOption.DB_RECORD_DISABLED in flags

        self._partial_pgn_disabled = Enums.BoardOption.PARTIAL_PGN_DISABLED in flags

        self._resume_disabled = Enums.BoardOption.RESUME_DISABLED in flags

        self._dal = DAL.get()

        self._dal.set_read_only(db_record_disabled)


    def _on_socket_request(self, data, socket):

        # Common sys requests handling
        sys_requests.handle_socket_requests(data)

        if not self._initialized or not self._started:
            return

        try:
            response = {}

            if "pgn" in data:
                response["pgn"] = self.get_current_pgn()
                socket.send_web_message(response)
                del data["pgn"]

            if "fen" in data:
                response["fen"] = self._chessboard.fen()
                socket.send_web_message(response)
                del data["fen"]

            if "uci_move" in data:
                response["uci_move"] = self.last_uci_move
                socket.send_web_message(response)
                del data["uci_move"]

            if "web_menu" in data:
                self.initialize_web_menu()
                del data["web_menu"]

            if "web_move" in data:
                # A move has been triggered from web UI
                CENTAUR_BOARD.move_piece(common.Converters.to_square_index(data["web_move"].get("source", None)), Enums.PieceAction.LIFT)
                
                if not CENTAUR_BOARD.move_piece(common.Converters.to_square_index(data["web_move"].get("target", None)), Enums.PieceAction.PLACE):
                    response["fen"] = self._chessboard.fen()
                    socket.send_web_message(response)

                del data["web_move"]

            if "web_button" in data:
                CENTAUR_BOARD.push_button(Enums.Btn(data["web_button"]))
                del data["web_button"]

            if self._socket_callback:

                self._socket_callback(data, socket)

        except Exception as e:
            Log.exception(Engine._on_socket_request, e)
            pass

    @staticmethod
    def __invoke_callback(callback, **args):
        if callback != None:
            try:
                Log.debug(f"{Engine.__invoke_callback.__name__}[{callback.__name__}({args})]")
                return callback(**args)
            except Exception as e:
                Log.exception(Engine.__invoke_callback, e)
        else:
            return True

    def __initialize(self):

        CENTAUR_BOARD.leds_off()

        self._computer_uci_move = ""
        self._computer_move_is_ready = False
        self._san_move_list = []
        self._piece_handler = PieceHandler(self)

        self._new_evaluation_requested = False

    def __key_callback(self, key:Enums.Btn):

        if not self._started:
            return

        if Engine.__invoke_callback(self._key_callback_function, key=key) == False:
            # Key has not been handled by the client!

            # Default tick key
            # Disable/Enable evaluation
            if not self._evaluation_disabled and key == Enums.Btn.TICK:
                self._show_evaluation = not self._show_evaluation

                self.update_evaluation(force=True, text="evaluation enabled" if self._show_evaluation else "evaluation disabled")

                self.update_evaluation()

                self.display_partial_PGN()
                self.display_board()

            # Default up key
            # Resign
            if key == Enums.Btn.UP:
                CENTAUR_BOARD.beep(Enums.Sound.COMPUTER_MOVE)
                SCREEN.draw_resignation_window()

                def wait_for_resignation_input():

                    def _confirm_key_callback(key:Enums.Btn):

                        if key == Enums.Btn.TICK:
                            # Back to original callbacks
                            CENTAUR_BOARD.unsubscribe_events()
                            self.display_board()
                            self.end()
                            self.stop()
                            return

                        if key == Enums.Btn.BACK:
                            # Back to original callbacks
                            CENTAUR_BOARD.unsubscribe_events()
                            self.display_board()
                            return

                    # We temporary disable the board field callback
                    # and we add a new temporary board key callback
                    CENTAUR_BOARD.subscribe_events(_confirm_key_callback)

                wait_for_resignation_input()

            # Default exit key
            if key == Enums.Btn.BACK:
                
                self.end()
                self.stop()
        
            # Default down key
            # Show previous move
            if key == Enums.Btn.DOWN:

                if self._previous_move_displayed:

                     self._previous_move_displayed = False
                     
                     if self._computer_move_is_ready:
                        self.set_computer_move(self._computer_uci_move)
                          
                     else:
                        CENTAUR_BOARD.leds_off()

                else:

                    # We read the last move that has been recorded
                    previous_uci_move = self.last_uci_move

                    if previous_uci_move:
                        from_num = common.Converters.to_square_index(previous_uci_move, Enums.SquareType.ORIGIN)
                        to_num = common.Converters.to_square_index(previous_uci_move, Enums.SquareType.TARGET)

                        CENTAUR_BOARD.led_from_to(from_num,to_num)

                        self.send_message_to_web_ui({
                            "clear_board_graphic_moves":False,
                            "uci_move":previous_uci_move,
                        })

                        self._previous_move_displayed = True

    # Receives field events from the board.
    # Positive is a field lift, negative is a field place.
    # Numbering 0 = a1, 63 = h8
    def __field_callback(self, field_index, field_action, web_move = False) -> bool:

        if not self._initialized or not self._started:
            return False

        self._previous_move_displayed = False
        try:
            result = self._piece_handler(field_index, field_action, web_move)

            # The board has not been physically updated.
            # We don't care about the board state...
            if web_move:
                self._invalid_board_state = False

            return result

        except Exception as e:
            Log.exception(Engine.__field_callback, e)
            return False

    def _check_last_move_outcome_and_switch(self):
        # Check the outcome
        outcome = self._chessboard.outcome(claim_draw=True)
        if outcome == None or outcome == "None" or outcome == 0:
            # Switch the turn
            Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.PLAY, outcome=None)
        else:
            # Depending on the outcome we can update the game information for the result
            self._dal.terminate_game(str(self._chessboard.result()))

            str_outcome = {

                    chess.Termination.CHECKMATE:"checkmate",
                    chess.Termination.STALEMATE:"stalemate",
                    chess.Termination.INSUFFICIENT_MATERIAL:"draw",
                    chess.Termination.SEVENTYFIVE_MOVES:"draw",
                    chess.Termination.FIVEFOLD_REPETITION:"draw",
                    chess.Termination.FIFTY_MOVES:"draw",
                    chess.Termination.THREEFOLD_REPETITION:"draw",
                    chess.Termination.VARIANT_WIN:"draw",
                    chess.Termination.VARIANT_LOSS:"draw",
                    chess.Termination.VARIANT_DRAW:"draw",
        
                }[outcome.termination]
            
            self.update_evaluation(force=True, text=str_outcome)

            self.send_message_to_web_ui({ 
                "turn_caption":str_outcome
            })

            Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.TERMINATION, outcome=outcome)

    def _evaluation_thread_instance(self):

        try:
            while self._started:

                if self._new_evaluation_requested and self._initialized:

                    self._new_evaluation_requested = False

                    if self._show_evaluation and not self._evaluation_disabled:

                        def evaluation_callback(results:Tuple[ChessEngine.TAnalyseResult, ...]):

                            result = results[0]

                            mate = result.score.pov(chess.WHITE).mate()

                            if mate != None:
                                    mate = abs(mate)

                                    if mate == 0:
                                        self.update_evaluation(force=True, text="checkmate")
                                    else:
                                        self.update_evaluation(force=True, text=f"mate in {mate}")
                            else:
                                expectation = result.score.pov(chess.WHITE).wdl().expectation()

                                self.update_evaluation(force=True, expectation=expectation)

                        self.chess_engine.analyse(
                            self._chessboard, 
                            chess.engine.Limit(time=1), 
                            on_analyse_done = evaluation_callback)

                    else:
                        self.update_evaluation(force=True, disabled=True)

                time.sleep(.5)

        except Exception as e:
            Log.exception(Engine._evaluation_thread_instance, e)

    def _game_thread_instance_worker(self):
        # The main thread handles the actual chess game functionality and calls back to
        # eventCallback with game events and
        # moveCallback with the actual moves made

        CENTAUR_BOARD.leds_off()
        CENTAUR_BOARD.subscribe_events(self.__key_callback, self.__field_callback)

        self._dal.delete_empty_games()
        
        ticks = -1

        try:
            while self._started:

                # First time we are here
                # We might need to resume a game...
                if ticks == -1:

                    uci_moves_history = self._uci_moves_at_start if len(self._uci_moves_at_start)>0 else self._dal.read_uci_moves_history()

                    if not self._resume_disabled and len(uci_moves_history) > 0:

                        Log.info("RESUMING LAST GAME!")

                        self.__initialize()
                        
                        try:

                            last_uci_move = None

                            # We replay the previous game
                            for uci_move in uci_moves_history:

                                last_uci_move = uci_move

                                if len(uci_move)>3:
                                    try:
                                        move = self._chessboard.parse_uci(uci_move)
                                        san_move = self._chessboard.san(move)

                                        self._chessboard.push(move)

                                        self._san_move_list.append(san_move)
                                    except:
                                        pass
                            
                            del uci_moves_history

                            if self._chessboard.is_game_over():
                                self._need_starting_position_check = True
                                Log.info("LAST GAME WAS FINISHED!")
                            
                            else:
                                CENTAUR_BOARD.beep(Enums.Sound.MUSIC)

                                self._update_board_state(False)

                                common.update_Centaur_FEN(self._chessboard.fen())

                                self.display_board()
                                self.display_partial_PGN()

                                self.update_web_ui({ 
                                    "clear_board_graphic_moves":True,
                                    "uci_move":last_uci_move })

                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.RESUME_GAME, outcome=None)
                                
                                self.update_evaluation()

                                self._check_last_move_outcome_and_switch()
                            
                                self._initialized = True

                        except Exception as e:
                            Log.exception(Engine._game_thread_instance_worker, e)

                # Detect if a new game has begun
                if self._need_starting_position_check:

                    if ticks < 5:
                        ticks = ticks + 1
                    else:
                        try:

                            board_state = CENTAUR_BOARD.get_board_state()

                            # In case of full undo we do not restart a game - no need
                            if bytearray(board_state) == consts.BOARD_START_STATE:
                                
                                Log.info("STARTING A NEW GAME!")

                                del board_state

                                SCREEN.clear_area()

                                #all_objects = muppy.get_objects()
                                #global_len = len(all_objects)
                                #print(f"Global size:{global_len}")
                                #sum1 = summary.summarize(all_objects)
                                #summary.print_(sum1)

                                self._invalid_board_state = False
                                self._need_starting_position_check = False

                                self._chessboard.reset()
                                
                                self.__initialize()
                                
                                CENTAUR_BOARD.beep(Enums.Sound.MUSIC)

                                common.update_Centaur_FEN(self._chessboard.fen())
                                
                                self.display_board()
                                self.display_partial_PGN()
                                self.update_web_ui({ 
                                    "clear_board_graphic_moves":True
                                })

                                # Log a new game in the db
                                self._dal.insert_new_game(
                                    source = self.source,
                                    event  = self._game_informations.get("event",""),
                                    site   = self._game_informations.get("site",""),
                                    round  = self._game_informations.get("round",""),
                                    white  = self._game_informations.get("white","Player white"),
                                    black  = self._game_informations.get("black","Player black")
                                )

                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.NEW_GAME, outcome=None)
                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.PLAY, outcome=None)
                                
                                self._initialized = True

                                self.update_evaluation()
                            
                            ticks = 0
                        except:
                            pass

                time.sleep(.1)

        except Exception as e:
            Log.exception(Engine._game_thread_instance_worker, e)

    @property
    def computer_uci_move(self) -> str:
        """Computer's choice of move, stripping off promotion suffix"""
        return self._computer_uci_move[0:4]

    @property
    def chess_engine(self):

        # By default we use Stockfish engine.
        if self._chess_engine is None:
            self._chess_engine = ChessEngine.get(consts.STOCKFISH_ENGINE_PATH)

        return self._chess_engine

    def initialize_web_menu(self):

        SOCKET.send_web_message({ 
            "update_menu": menu.get(menu.Tag.ONLY_WEB, ["homescreen", "links", "settings", "system"])
        })
    
    @property
    def is_started(self):
        return self._started

    def start(self, uci_moves = []):

        if self._started:
            return
        
        self._started = True

        SOCKET.initialize(on_socket_request=self._on_socket_request)

        self._uci_moves_at_start = uci_moves
        
        self._need_starting_position_check = True

        self._game_thread_instance = Thread(target=self._game_thread_instance_worker)
        self._game_thread_instance.daemon = True
        self._game_thread_instance.start()

        self._evaluation_thread_instance = Thread(target=self._evaluation_thread_instance)
        self._evaluation_thread_instance.daemon = True
        self._evaluation_thread_instance.start()

        self.initialize_web_menu()

        Log.info(f"{Engine.__name__} thread started.")

    def end(self):
        Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.QUIT, outcome=None)

    def stop(self):
        
        if not self._started:
            return

        CENTAUR_BOARD.leds_off()
        self._started = False

        SOCKET.disconnect()

        try:
            self._game_thread_instance.join()
        except:
            pass

        try:
            self._evaluation_thread_instance.join()
        except:
            pass
        
        if self._chess_engine:
            self._chess_engine.quit()

        CENTAUR_BOARD.unsubscribe_events()

        LiveScript.detach_game_engine()

        Log.info(f"{Engine.__name__} thread has been stopped.")

    def cancel_evaluation(self):

        if not self._started:
            return

        self._new_evaluation_requested = False

    def update_evaluation(self, expectation:float=None, force:bool=False, text:str=None, disabled:bool=False):
        
        if not self._started:
            return
        
        if force:
            self._new_evaluation_requested = False
            SCREEN.draw_evaluation_bar(text=text, expectation=expectation, disabled=disabled)
        else:
            self._new_evaluation_requested = True

    def flash_hint(self, thinking_time = 1):

        if not self._started:
            return

        try:
            self.update_evaluation(force=True, text="thinking...")

            def hint_callback(results:Tuple[ChessEngine.TAnalyseResult, ...]):

                uci_hint_move = results[0].uci_move

                Log.info(f'Engine help requested :"{uci_hint_move}"')

                self.send_message_to_web_ui({ 
                    "tip_uci_move":uci_hint_move
                })

                if uci_hint_move!= None:
                    from_num = common.Converters.to_square_index(uci_hint_move, Enums.SquareType.ORIGIN)
                    to_num = common.Converters.to_square_index(uci_hint_move, Enums.SquareType.TARGET)

                    CENTAUR_BOARD.led_from_to(from_num,to_num)

                self.update_evaluation()

            self.chess_engine.analyse(self._chessboard, chess.engine.Limit(time=thinking_time), on_analyse_done=hint_callback)

        except Exception as e:
            Log.exception(Engine.flash_hint, e)
            pass

    @property
    def last_uci_move(self) -> Optional[str]:
        
        if not self._started:
            return None
        
        return None if self._chessboard.ply() == 0 else self._chessboard.peek().uci()

    @property
    def last_san_move(self) -> Optional[str]:

        if not self._started:
            return None

        try:
            move = self._chessboard.pop()
            san = self._chessboard.san(move)
            self._chessboard.push_san(san)

            return san

        except:
            return None

    def _update_board_state(self, web_move:bool):

        if not self._started or web_move:
            return

        board_state = CENTAUR_BOARD.get_board_state()

        # TODO: handle the bytearray exception.
        try:
            if bytearray(board_state) == consts.BOARD_START_STATE:
                self._need_starting_position_check = True
                return
        except:
            pass

        business_board_state = common.Converters.fen_to_board_state(self._chessboard.fen())
        invalid_squares = []
        for square in range(0,64):
            if business_board_state[square] != board_state[square]:
                invalid_squares.append(square)

        if len(invalid_squares):
            self._invalid_board_state = True
            CENTAUR_BOARD.led_array(invalid_squares, no_field_rotation=True)
        else:
            self._invalid_board_state = False
            CENTAUR_BOARD.leds_off()

    def display_board(self):

        if not self._started:
            return

        SCREEN.draw_fen(self._chessboard.fen(), startrow=1.6)

    def send_message_to_web_ui(self, message={}):
        # We send the message to all connected clients

        if not self._started:
            return

        if self._evaluation_disabled:
            message["evaluation_disabled"] = True

        SOCKET.send_web_message(message)

    def update_web_ui(self, args={}):
        # We send the new FEN to all connected clients

        if not self._started:
            return

        message = {**{
            "pgn":self.get_current_pgn(), 
            "fen":self._chessboard.fen(),
            "uci_move":self.last_uci_move,
            "checkers":list(map(lambda item:common.Converters.to_square_name(item), self._chessboard.checkers())),
            "kings":[common.Converters.to_square_name(self._chessboard.king(chess.WHITE)), common.Converters.to_square_name(self._chessboard.king(chess.BLACK))],
        }, **args}

        SOCKET.send_web_message(message)

    def get_current_pgn(self):

        current_pgn = ""

        if self._started:
            if len(self._san_move_list) > 0:

                # We always start to show a white move
                current_turn = chess.WHITE

                current_row_index = 1
        
                for san in self._san_move_list:

                    # White move
                    if current_turn == chess.WHITE:
                        if (san != None):
                            current_pgn = current_pgn + f"{current_row_index}. "+san

                    # Black move
                    else:
                        if san != None:
                            current_pgn = current_pgn + " "+ san + '\n'

                        current_row_index = current_row_index + 1

                    # We switch the color
                    current_turn = not current_turn

        return current_pgn
    
    def display_board_header(self, text):
        SCREEN.write_text(1, text, font=fonts.MEDIUM_MAIN_FONT)

    def display_partial_PGN(self, row=9.3, move_count=10):

        if not self._partial_pgn_disabled and self._started:

            # Maximum displayed moves
            move_count = 10

            # We read the last san moves
            san_list = self._san_move_list[-move_count:] if self._chessboard.turn == chess.WHITE else self._san_move_list[-move_count+1:]
            san_list = list(san_list) + ([None] * move_count)
            
            # We truncate the list
            del san_list[move_count:]

            # We always start to show a white move
            current_turn = chess.WHITE
            
            current_row_move = ""
            current_row_index = int((len(self._san_move_list) -move_count +1) / 2) +1
            current_row_index = 1 if current_row_index < 1 else current_row_index

            for san in san_list:

                # White move
                if current_turn == chess.WHITE:
                    if san == None:
                        SCREEN.write_text(row, consts.EMPTY_LINE, centered=False)
                    else:
                        current_row_move = f"{current_row_index}. "+san
                        SCREEN.write_text(row, current_row_move, centered=False)

                # Black move
                else:
                    if san != None:
                        current_row_move = current_row_move + ".."+san
                        SCREEN.write_text(row, current_row_move, centered=False)

                    row = row + 1
                    current_row_index = current_row_index + 1

                # We switch the color
                current_turn = not current_turn

    @property
    def chessboard(self):
        return self._chessboard
    
    @property
    def computer_move_is_ready(self):
        return self._computer_move_is_ready

    def set_computer_move(self, uci_move) -> bool:
            
        try:

            if not self._started:
                return False

            try:
                chess.Move.from_uci(uci_move)
            except:
                Log.debug(f'INVALID uci_computer_move:"{uci_move}"')
                return False
            
            if uci_move not in (str(move) for move in self._chessboard.legal_moves):
                Log.debug(f'ILLEGAL uci_computer_move:"{uci_move}"')
                return False
            
            Log.debug(f'uci_computer_move:"{uci_move}"')

            # First set the globals so that the thread knows there is a computer move
            self._computer_uci_move = uci_move
            self._computer_move_is_ready = True
            
            # Next indicate this on the board. First convert the text representation to the field number
            from_num = common.Converters.to_square_index(uci_move, Enums.SquareType.ORIGIN)
            to_num = common.Converters.to_square_index(uci_move, Enums.SquareType.TARGET)

            CENTAUR_BOARD.beep(Enums.Sound.COMPUTER_MOVE)
   
            # Then light it up!
            CENTAUR_BOARD.led_from_to(from_num,to_num)

            self.send_message_to_web_ui({ 
                "clear_board_graphic_moves":False,
                "computer_uci_move":uci_move,
            })

            return True
 
        except Exception as e:
            Log.exception(Engine.set_computer_move, e)
