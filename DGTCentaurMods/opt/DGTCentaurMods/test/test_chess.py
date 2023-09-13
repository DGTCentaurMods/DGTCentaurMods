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

import chess
import unittest


class TestChess(unittest.TestCase):
    """We use python-chess as a common interface to represent chess
    boards and moves and to manipulate games.  These tests are not
    to verify the library, but to document it and validate our usage
    of it."""

    def test_Colors(self):
        """Colors are represented as booleans, with the intent that you
        can toggle the color with `not`."""

        # chess.Color is a type synonym for bool
        self.assertEqual(chess.Color, bool)
        self.assertIsInstance(chess.BLACK, chess.Color)

        # chess.BLACK is False, chess.WHITE is True
        self.assertEqual(chess.BLACK, False)
        self.assertEqual(not chess.BLACK, chess.WHITE)

    def test_PieceTypes(self):
        """Piece typess are enumerated PAWN = 1, KNIGHT, BISHOP, ROOK,
        QUEEN, and KING."""

        # chess.PieceType is a type synonym for int
        self.assertEqual(chess.PieceType, int)
        self.assertIsInstance(chess.PAWN, chess.PieceType)

        # Pieces are enumerated
        self.assertEqual(chess.KNIGHT, 2)
        self.assertEqual(chess.KING, 6)

        # Use chess.piece_symbol to represent a piece as a string
        self.assertEqual(chess.piece_symbol(chess.KNIGHT), "n")

    def test_Pieces(self):
        """A piece has both a type and a color."""

        black_knight = chess.Piece(piece_type=chess.KNIGHT, color=chess.BLACK)
        self.assertEqual(black_knight.piece_type, chess.KNIGHT)
        self.assertEqual(black_knight.color, chess.BLACK)

        # White pieces are represented by upper case letters
        white_queen = chess.Piece(piece_type=chess.QUEEN, color=chess.WHITE)
        self.assertEqual(white_queen.symbol(), "Q")
        self.assertEqual(black_knight.symbol(), "n")

        self.assertEqual(white_queen, chess.Piece.from_symbol("Q"))
        self.assertEqual(black_knight, chess.Piece.from_symbol("n"))

        # May throw ValueError
        self.assertRaises(ValueError, chess.Piece.from_symbol, "z")

    def test_Squares(self):
        """Squares are enumerated from A1 = 0 to H8 = 63."""

        # chess.Square is a type synonym for int
        self.assertEqual(chess.Square, int)
        self.assertIsInstance(chess.A1, chess.Square)

        # Enumeration is row major, by rank and file
        self.assertEqual((chess.A1, chess.B1, chess.C1), (0, 1, 2))
        self.assertEqual((chess.A1, chess.A2, chess.A3), (0, 8, 16))

        # Convert between squares and algebraic names
        self.assertEqual(chess.square_name(chess.F6), "f6")
        self.assertEqual(chess.parse_square("f6"), chess.F6)

        # May throw ValueError
        self.assertRaises(ValueError, chess.parse_square, "z9")

        # Convert between squares and ranks and files
        self.assertEqual(chess.square_file(chess.F3), 5)
        self.assertEqual(chess.square_rank(chess.F3), 2)
        self.assertEqual(chess.square(file_index=5, rank_index=2), chess.F3)

    def test_Moves(self):
        """Represents a move from a source square to a target square,
        possibly promoting."""

        # Normal move without promotion
        kings_pawn = chess.Move(from_square=chess.E2, to_square=chess.E4)
        self.assertEqual(kings_pawn.from_square, chess.E2)
        self.assertEqual(kings_pawn.to_square, chess.E4)
        self.assertEqual(kings_pawn.promotion, None)

        # String representation is from Universal Chess Interface
        self.assertEqual(kings_pawn.uci(), "e2e4")
        self.assertEqual(chess.Move.from_uci("e2e4"), kings_pawn)

        # Promotion
        promotion = chess.Move.from_uci("e7e8q")
        self.assertEqual(promotion.promotion, chess.QUEEN)

        # Note that promotion does not recognize piece color
        self.assertRaises(ValueError, chess.Move.from_uci, "e7e8Q")


class TestBoard(unittest.TestCase):
    """Separating out the tests for chess.Board, because it is a big
    class that does a lot.  It maintains the current state of the board
    and the move history, checks and validates attempted moves, and also
    provides a few conversion utilities."""

    def test_StartingBoard(self):
        """Test board attributes from known starting position."""

        board = chess.Board()
        self.assertEqual(board.turn, chess.WHITE)
        self.assertEqual(board.move_stack, [])
        self.assertEqual(len(list(board.legal_moves)), 20)

        # Examine pieces
        self.assertEqual(board.piece_at(chess.E8), chess.Piece.from_symbol("k"))
        self.assertEqual(board.piece_type_at(chess.E8), chess.KING)
        self.assertEqual(board.color_at(chess.E8), chess.BLACK)
        self.assertEqual(board.king(chess.BLACK), chess.E8)

    def test_Promotion(self):
        """Legal board moves include all possible promotions."""

        # White pawn on king's rook 7
        board = chess.Board(fen="4k3/7P/8/8/8/8/4K3/8 w - - 0 1")
        self.assertEqual(board.fen(), "4k3/7P/8/8/8/8/4K3/8 w - - 0 1")

        self.assertIn(chess.Move.from_uci("h7h8n"), board.legal_moves)
        self.assertIn(chess.Move.from_uci("h7h8b"), board.legal_moves)
        self.assertIn(chess.Move.from_uci("h7h8r"), board.legal_moves)
        self.assertIn(chess.Move.from_uci("h7h8q"), board.legal_moves)
        self.assertEqual(board.find_move(chess.H7, chess.H8, chess.QUEEN),
                         chess.Move.from_uci("h7h8q"))

    def test_SAN(self):
        """Convert to/from Standard Algebraic Notation."""

        # White pawn on king's rook 7
        board = chess.Board(fen="4k3/7P/8/8/8/8/4K3/8 w - - 0 1")
        move = chess.Move(chess.H7, chess.H8, promotion=chess.KNIGHT)
        self.assertEqual(board.san(move), "h8=N")
        self.assertEqual(board.parse_san("h8=N"), move)

    def test_Move(self):
        board = chess.Board()
        move = chess.Move(chess.E2, chess.E4)

        # Make move
        board.push(move)
        self.assertEqual(board.board_fen(), "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR")

        # Access last move
        self.assertEqual(board.peek(), move)
        self.assertEqual(board.peek().uci(), "e2e4")
        self.assertEqual(board.move_stack[-1], move)

        # Undo move
        board.pop()

        # Make move in UCI
        board.push_uci("e2e4")
        self.assertEqual(board.peek(), move)
        board.pop()

        # Make move in SAN
        board.push_san("e4")
        self.assertEqual(board.peek().uci(), "e2e4")
        board.pop()

        # Rejects illegal moves
        board = chess.Board()
        self.assertRaises(ValueError, board.push_uci, "c1a3")
