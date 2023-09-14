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

from DGTCentaurMods.consts import Enums, consts
from DGTCentaurMods.lib import common

import chess
import os
import unittest


# Hook to run doctests from unittest
def load_tests(loader, tests, ignore):
    import doctest
    tests.addTests(doctest.DocTestSuite(common))
    return tests


class TestSingleton(unittest.TestCase):

        def test_Singleton1(self):
            """Attempts to instantiate a Singleton yield same object."""

            class Derived(common.Singleton):
                 pass

            # Both refer to same object
            ref1 = Derived()
            ref2 = Derived()
            self.assertIs(ref1, ref2)

            # In case we're not sure if we believe "is"
            ref1.test_attribute = "this is a test"
            self.assertEqual(ref2.test_attribute, "this is a test")

        def test_Singleton2(self):
            """Derived classes are kept separate."""

            class Derived1(common.Singleton):
                pass

            class Derived2(common.Singleton):
                pass

            ref1 = Derived1()
            ref2 = Derived2()
            self.assertIsNot(ref1, ref2)

            ref1.test_attribute = "this is a test"
            self.assertIsNone(getattr(ref2, "test_attribute", None))


class TestCommon(unittest.TestCase):

    def test_capitalize_string(self):
        """Capitalize first letter of string, preserving existing capitals."""
        self.assertEqual(common.capitalize_string("my Turn"), "My Turn")

        # N.B., str.capitalize() does not preserve existing capitals
        self.assertEqual("my Turn".capitalize(), "My turn")

    def test_tail(self):
        """Read lines from end of file."""

        license = """
  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<http://www.gnu.org/philosophy/why-not-lgpl.html>.
"""
        expected = license.splitlines(keepends=True)
        with open("../../../LICENSE.md", "r") as f:
            actual = common.tail(f, len(expected))
        self.assertEqual(expected, actual)

    def test_FEN(self):
        """Exercise FEN log."""

        # Generate a non-default FEN
        board = chess.Board()
        board.push_san("e4")
        expected = board.fen()

        # Ensure log directory exists
        os.makedirs(os.path.dirname(consts.FEN_LOG), exist_ok=True)

        # Write FEN to log
        common.update_Centaur_FEN(expected)

        # Read last logged FEN
        actual = common.get_Centaur_FEN()

        self.assertEqual(expected, actual)


class TestConverters(unittest.TestCase):

    def test_to_square_name(self):
        """Convert a square index to a square name."""
        self.assertEqual(common.Converters.to_square_name(chess.A1), "a1")
        self.assertEqual(common.Converters.to_square_name(chess.H8), "h8")
        self.assertEqual(common.Converters.to_square_name(chess.D4), "d4")

    def test_to_square_index(self):
        """Convert a UCI move to an index of one of its squares."""

        # Move origin
        self.assertEqual(
            common.Converters.to_square_index("g1f3", Enums.SquareType.ORIGIN),
            chess.G1)
        self.assertEqual(
            common.Converters.to_square_index("c1a3", Enums.SquareType.ORIGIN),
            chess.C1)
        self.assertEqual(
            common.Converters.to_square_index("b8c7", Enums.SquareType.ORIGIN),
            chess.B8)

        # Move target
        self.assertEqual(
            common.Converters.to_square_index("g1f3", Enums.SquareType.TARGET),
            chess.F3)
        self.assertEqual(
            common.Converters.to_square_index("c1a3", Enums.SquareType.TARGET),
            chess.A3)
        self.assertEqual(
            common.Converters.to_square_index("b8c7", Enums.SquareType.TARGET),
            chess.C7)
