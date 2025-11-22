"""Tests for game_engine.py"""

import os
import sys
import pytest
import builtins

# ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from game_engine import (
    parse_letter_number_input,
    cli_coords_input,
    other_colour,
    simple_game_loop,
)

from components import (
    initialise_board,
)

class TestParseLetterNumberInput:
    """Tests for parsing letter number input"""

    def test_basic_valid_inputs(self):
        """Basic valid inputs should parse correctly"""
        assert parse_letter_number_input("A1") == (1, 1)
        assert parse_letter_number_input("H8") == (8, 8)
        assert parse_letter_number_input("C4") == (3, 4)

    def test_valid_inputs_with_spaces_and_mixed_case(self):
        """Inputs with spaces or mixed case should still parse correctly"""
        assert parse_letter_number_input("a 3") == (1, 3)
        assert parse_letter_number_input("D 6") == (4, 6)
        assert parse_letter_number_input("  h8 ") == (8, 8)
        assert parse_letter_number_input(" c 4 ") == (3, 4)

    def test_valid_inputs_with_commas(self):
        """Formats with commas should be accepted and parsed correctly."""
        assert parse_letter_number_input("A, 3") == (1, 3)
        assert parse_letter_number_input("d,7") == (4, 7)

    def test_invalid_when_missing_number(self):
        """Inputs missing a number should raise ValueError."""
        with pytest.raises(ValueError):
            parse_letter_number_input("A")

    def test_invalid_when_non_letter_as_first_char(self):
        """First character must be A–H, anything else should raise ValueError."""
        with pytest.raises(ValueError):
            parse_letter_number_input("1A")
        with pytest.raises(ValueError):
            parse_letter_number_input("$3")
        with pytest.raises(ValueError):
            parse_letter_number_input("Z9")

    def test_invalid_when_row_not_number(self):
        """Row must be numeric, symbols or letters should raise ValueError."""
        with pytest.raises(ValueError):
            parse_letter_number_input("A?")
        with pytest.raises(ValueError):
            parse_letter_number_input("C:")
        with pytest.raises(ValueError):
            parse_letter_number_input("DxAD3")

    def test_invalid_row_range(self):
        """Row must be between 1–8, values outside this range should raise ValueError."""
        with pytest.raises(ValueError):
            parse_letter_number_input("A0")
        with pytest.raises(ValueError):
            parse_letter_number_input("H9")
        with pytest.raises(ValueError):
            parse_letter_number_input("B12")


class TestCLICoordsInput:
    """Tests for CLI coordintes input."""

    def test_valid_input_first_try(self, monkeypatch):
        """CLI accepts valid input immediately."""
        monkeypatch.setattr("builtins.input", lambda _: "C4")

        assert cli_coords_input() == (3, 4)

    def test_invalid_then_valid_input(self, monkeypatch):
        """CLI retries when input is invalid, then succeeds with a valid move."""
        inputs = iter(["Z9", "A0", "B3"])  # first two invalid, third valid

        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        assert cli_coords_input() == (2, 3)  # B3

    def test_input_with_spaces_and_weird_format(self, monkeypatch):
        """CLI accepts inputs like '  d  6 ' after parsing/cleaning."""
        monkeypatch.setattr("builtins.input", lambda _: "  d  6 ")

        assert cli_coords_input() == (4, 6)

    def test_quit_lowercase(self, monkeypatch):
        """Entering 'q' exits the program with SystemExit."""
        monkeypatch.setattr("builtins.input", lambda _: "q")

        with pytest.raises(SystemExit):
            cli_coords_input()

    def test_quit_uppercase(self, monkeypatch):
        """Entering 'QUIT' in uppercase also exits."""
        monkeypatch.setattr("builtins.input", lambda _: "QUIT")

        with pytest.raises(SystemExit):
            cli_coords_input()

    def test_quit_full_word(self, monkeypatch):
        """Entering 'exit' also exits."""
        monkeypatch.setattr("builtins.input", lambda _: "exit")

        with pytest.raises(SystemExit):
            cli_coords_input()

    def test_multiple_invalid_before_quit(self, monkeypatch):
        """CLI should allow multiple invalid inputs before a quit command."""
        inputs = iter(["???", "A", "D0", "q"])

        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        with pytest.raises(SystemExit):
            cli_coords_input()


class TestOtherColour:
    """
    Trivial tests, acting purely as a sanity check

    Due to the nature of game_engine.py, other_colour will never have
    invalid args, so they're not worth testing for nor is it worth
    implementing .strip() or catching ValueError
    """
    def test_other_colour_black_to_white(self):
        """Black should map to White."""
        assert other_colour("Black") == "White"

    def test_other_colour_white_to_black(self):
        """White should map to Black."""
        assert other_colour("White") == "Black"


class TestSimpleGameLoop:
    """Test the simple game loop."""

    def test_simple_game_loop_no_moves_draw(self, monkeypatch, capsys):
        """
        Game ends immediately when neither Black nor White
        has any legal moves. Should print a draw result.
        """
        # ensure no one has any legal moves
        def always_no_moves(colour, board):
            return False

        monkeypatch.setattr("game_engine.has_any_legal_moves", always_no_moves)

        # make counting pieces deterministic: equal pieces -> draw
        def fake_count_pieces(board):
            return (2, 2)

        monkeypatch.setattr("game_engine.count_pieces", fake_count_pieces)

        # cli_coords_input should never be called in this scenario
        # but patch it just in case (so test fails loudly if it is)
        def fake_cli():
            raise AssertionError("cli_coords_input should not be called")

        monkeypatch.setattr("game_engine.cli_coords_input", fake_cli)

        # run the loop
        simple_game_loop()

        # capture the printed output
        captured = capsys.readouterr().out

        assert "Welcome to Othello" in captured
        assert "Black moves first" in captured
        assert "has no legal moves." in captured
        assert "Game over!" in captured
        assert "Black: 2, White: 2" in captured
        assert "It's a draw!" in captured

    def test_simple_game_loop_pass_and_single_move(self, monkeypatch, capsys):
        """
        Black starts with no moves and passes. White then makes one move,
        after which both player have no legal moves and the game ends.
        """
        moved = False

        def fake_has_any_legal_moves(colour, board):
            # Before the first (and only) move, only White can move.
            # after that move, nobody has any legal moves.
            if not moved:
                return colour == "White"
            return False

        monkeypatch.setattr(
            "game_engine.has_any_legal_moves", fake_has_any_legal_moves
        )

        # always accept the first coordinate as a legal move
        # this should only trigger for white as only white has legal moves
        def fake_legal_move(colour, coord, board):
            return True

        monkeypatch.setattr("game_engine.legal_move", fake_legal_move)

        # apply_move marks that a move has happened and returns 1 flip
        def fake_apply_move(colour, coord, board):
            moved = True
            return 1

        monkeypatch.setattr("game_engine.apply_move", fake_apply_move)

        # coordinates for white's move
        def fake_cli_coords_input():
            return (3, 4)

        monkeypatch.setattr("game_engine.cli_coords_input", fake_cli_coords_input)

        # choose a winner for the final count
        def fake_count_pieces(board):
            # hlack wins
            return (5, 3)

        monkeypatch.setattr("game_engine.count_pieces", fake_count_pieces)

        # run the game
        simple_game_loop()

        captured = capsys.readouterr().out

        assert "Welcome to Othello" in captured
        assert "Black moves first" in captured

        assert "Black has no legal moves and passes." in captured

        assert "White's turn!" in captured
        assert "Move applied - 1 discs flipped." in captured

        # game should end after that move when no one has any moves
        assert "Game over!" in captured
        assert "Black: 5, White: 3" in captured
        assert "Black wins!" in captured

    def test_fastest_game(self, monkeypatch, capsys):
        """Simulates the fastest sequence of moves to end the game possible"""
        moves = iter([
            "E6",
            "F4",
            "E3",
            "F6",
            "G5",
            "D6",
            "E7",
            "F5",
            "C5",
        ])

        def fake_input(prompt: str = "") -> str:
            # return the next move each time input() is called
            return next(moves)

        monkeypatch.setattr(builtins, "input", fake_input)

        # run the game loop with the scripted moves
        simple_game_loop()

        # capture printed output
        captured = capsys.readouterr()

        # checks game ends and a result is printed
        assert "Game over" in captured.out
        assert "Black:" in captured.out
        assert "White:" in captured.out
        # someone wins
        assert "wins!" in captured.out