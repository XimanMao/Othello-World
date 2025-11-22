"""Tests for components.py"""

import io
import os
import sys

# ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from contextlib import redirect_stdout
from components import (
    initialise_board,
    print_board,
    _discs_to_flip,
    legal_move,
    apply_move,
    has_any_legal_moves,
    count_pieces,
    EMPTY,
    BLACK,
    WHITE,
)


class TestInitialiseBoard:
    """Tests for board initialisation."""

    def test_initialise_board_default_size(self):
        """Board should start as 8x8 with the correct initial 4 discs placed."""
        board = initialise_board()

        assert len(board) == 8
        assert all(len(row) == 8 for row in board)

        # correct initial configuration
        assert board[3][3] == WHITE
        assert board[4][4] == WHITE
        assert board[3][4] == BLACK
        assert board[4][3] == BLACK

        # all other squares must be empty
        for y in range(8):
            for x in range(8):
                if (x, y) not in [(3, 3), (4, 4), (3, 4), (4, 3)]:
                    assert board[y][x] == EMPTY

    def test_initialise_board_custom_size_4x4(self):
        """Board should initialise correctly for arbitrary even sizes like 4x4."""
        board = initialise_board(4)

        assert len(board) == 4
        assert all(len(row) == 4 for row in board)

        # midpoints for a 4×4 board
        assert board[1][1] == WHITE
        assert board[2][2] == WHITE
        assert board[1][2] == BLACK
        assert board[2][1] == BLACK

        # everything else empty
        for y in range(4):
            for x in range(4):
                if (x, y) not in [(1, 1), (2, 2), (1, 2), (2, 1)]:
                    assert board[y][x] == EMPTY


class TestPrintBoard:
    """Tests for board printing."""

    def test_print_board_output_format(self):
        """Ensure ASCII board output prints correct rows, separators, and labels."""
        board = initialise_board()
        buf = io.StringIO()

        with redirect_stdout(buf):
            print_board(board)

        output = buf.getvalue().splitlines()

        # should print: 8 rows, separator, bottom coordinate row
        assert len(output) == 10

        # basic formatting: row numbers + column letters
        assert output[0].startswith(" 1 |")
        assert output[-1].strip().startswith("A")

        # check specific rows in the initial setup
        assert output[3] == " 4 | .  .  .  W  B  .  .  . "
        assert output[4] == " 5 | .  .  .  B  W  .  .  . "


class TestDiscsToFlip:
    """Tests for disc flipping logic."""

    def test_discs_to_flip_black_initial_legal_moves(self):
        """black's four legal opening moves should flip exactly one disc each."""
        board = initialise_board()

        assert _discs_to_flip(board, BLACK, 2, 3) == [(3, 3)]
        assert _discs_to_flip(board, BLACK, 3, 2) == [(3, 3)]
        assert _discs_to_flip(board, BLACK, 4, 5) == [(4, 4)]
        assert _discs_to_flip(board, BLACK, 5, 4) == [(4, 4)]

    def test_discs_to_flip_white_initial_legal_moves(self):
        """white's four legal opening moves should flip exactly one disc each."""
        board = initialise_board()

        assert _discs_to_flip(board, WHITE, 2, 4) == [(3, 4)]
        assert _discs_to_flip(board, WHITE, 3, 5) == [(3, 4)]
        assert _discs_to_flip(board, WHITE, 4, 2) == [(4, 3)]
        assert _discs_to_flip(board, WHITE, 5, 3) == [(4, 3)]

    def test_discs_to_flip_out_of_bounds(self):
        """Moves outside the board should always return zero flips."""
        board = initialise_board()

        assert _discs_to_flip(board, BLACK, -1, 0) == []
        assert _discs_to_flip(board, BLACK, 0, -1) == []

        assert _discs_to_flip(board, BLACK, 8, 0) == []
        assert _discs_to_flip(board, BLACK, 0, 8) == []

    def test_discs_to_flip_on_occupied_square(self):
        """Moves on non-empty squares are illegal and flip nothing."""
        board = initialise_board()

        assert _discs_to_flip(board, BLACK, 3, 3) == []
        assert _discs_to_flip(board, WHITE, 3, 3) == []

    def test_discs_to_flip_invalid_colour(self):
        """Invalid player colours should produce no flips."""
        board = initialise_board()

        assert _discs_to_flip(board, "Green", 2, 3) == []
        assert _discs_to_flip(board, "", 2, 3) == []

    def test_discs_to_flip_no_bracketing_discs(self):
        """Legal moves that don't bracket opponent discs should flip none."""
        board = initialise_board()

        assert _discs_to_flip(board, BLACK, 0, 0) == []
        assert _discs_to_flip(board, WHITE, 7, 7) == []

    def test_discs_to_flip_complex_line_breaks(self):
        """
        Ensure sequences with gaps (e.g., B . W) do not incorrectly flip discs,
        since no continuous line of opponents is bracketed.
        """
        board = [[EMPTY for _ in range(8)] for _ in range(8)]

        board[3][1] = BLACK
        board[3][3] = WHITE

        assert _discs_to_flip(board, BLACK, 3, 4) == []


class TestLegalMove:
    """Tests for checking move legality."""

    def test_legal_moves_initial_black(self):
        """
        On the standard initial board, Black's legal moves are:
        C4, D3, E6, F5  -> (3,4), (4,3), (5,6), (6,5)
        using (x, y) with 1-based indexing.
        """
        board = initialise_board()

        assert legal_move("Black", (3, 4), board)
        assert legal_move("Black", (4, 3), board)
        assert legal_move("Black", (5, 6), board)
        assert legal_move("Black", (6, 5), board)

        assert not legal_move("Black", (1, 1), board)
        assert not legal_move("Black", (8, 8), board)

    def test_legal_moves_initial_white(self):
        """
        On the standard initial board, White's legal moves are:
        C5, D6, E3, F4  => (3,5), (4,6), (5,3), (6,4)
        """
        board = initialise_board()

        assert legal_move("White", (3, 5), board)
        assert legal_move("White", (4, 6), board)
        assert legal_move("White", (5, 3), board)
        assert legal_move("White", (6, 4), board)

        assert not legal_move("White", (1, 1), board)

    def test_move_on_occupied_square_is_illegal(self):
        """Tests that moves on occupied squares are illegal."""
        board = initialise_board()

        assert not legal_move("Black", (4, 4), board)
        assert not legal_move("White", (5, 5), board)
        assert not legal_move("Black", (4, 5), board)
        assert not legal_move("White", (5, 4), board)

    def test_out_of_bounds_moves_are_illegal(self):
        """Tests that moves on out of bounds moves are illegal."""
        board = initialise_board()

        assert not legal_move("Black", (0, 4), board)
        assert not legal_move("Black", (9, 4), board)
        assert not legal_move("Black", (4, 0), board)
        assert not legal_move("Black", (4, 9), board)

    def test_move_that_flips_no_discs_is_illegal(self):
        """Moves that flip no discs are illegal."""
        board = initialise_board()

        assert not legal_move("Black", (1, 1), board)
        assert not legal_move("White", (8, 8), board)

    def test_invalid_colour_is_illegal(self):
        """Testing that an invalid colour is illegal."""
        board = initialise_board()

        assert not legal_move("Red", (3, 4), board)
        assert not legal_move("", (3, 4), board)

        assert legal_move(" Black ", (3, 4), board)

    def test_legal_move_after_some_play(self):
        """Play a move and ensure new legal moves update correctly."""
        board = initialise_board()

        assert legal_move("Black", (3, 4), board)
        flipped = apply_move("Black", (3, 4), board)
        assert flipped > 0

        assert legal_move("White", (3, 3), board)


class TestApplyMove:
    """Tests for applying moves."""

    def test_apply_move_black_initial_position(self):
        """
        From the standard initial board, Black plays C4 (3,4).
        This should flip the White disc at D4 (4,4).
        """
        board = initialise_board()

        black_before, white_before = count_pieces(board)
        assert (black_before, white_before) == (2, 2)

        flipped = apply_move("Black", (3, 4), board)

        assert flipped == 1
        assert board[3][2].strip() == "Black"
        assert board[3][3].strip() == "Black"

        black_after, white_after = count_pieces(board)
        assert (black_after, white_after) == (4, 1)

    def test_apply_move_white_initial_position(self):
        """
        White plays C5 (3,5).
        Should flip Black at D5 (4,5).
        """
        board = initialise_board()

        black_before, white_before = count_pieces(board)
        assert (black_before, white_before) == (2, 2)

        flipped = apply_move("White", (3, 5), board)

        assert flipped == 1
        assert board[4][2].strip() == "White"
        assert board[4][3].strip() == "White"

        black_after, white_after = count_pieces(board)
        assert (black_after, white_after) == (1, 4)

    def test_apply_move_flips_multiple_discs_in_line(self):
        """
        Custom position: multiple discs flipped in one direction.
        """
        size = 8
        board = [[EMPTY for _ in range(size)] for _ in range(size)]

        board[3][1] = WHITE
        board[3][2] = BLACK
        board[3][3] = BLACK

        flipped = apply_move("White", (5, 4), board)

        assert flipped == 2
        assert board[3][4].strip() == "White"
        assert board[3][2].strip() == "White"
        assert board[3][3].strip() == "White"

    def test_apply_move_does_not_change_unrelated_squares(self):
        """Only relevant squares should be changed."""
        board = initialise_board()

        before_a1 = board[0][0]
        before_h8 = board[7][7]

        apply_move("Black", (3, 4), board)

        assert board[0][0] == before_a1
        assert board[7][7] == before_h8


class TestHasAnyLegalMoves:
    """Testing check for if there are any legal moves"""

    def test_has_any_legal_moves_starting_position(self):
        """
        In standard Othello starting position, both Black and White
        should have at least one legal move.
        """
        board = initialise_board()

        assert has_any_legal_moves("Black", board)
        assert has_any_legal_moves("White", board)

    def test_has_any_legal_moves_no_moves(self, monkeypatch):
        """
        Patch legal_move so that no moves are legal.
        This ensures the function correctly returns False.
        """
        board = initialise_board()

        def always_false(colour, coord, board):
            return False

        # patch the name that has_any_legal_moves actually calls
        monkeypatch.setattr("components.legal_move", always_false)

        assert not has_any_legal_moves("Black", board)
        assert not has_any_legal_moves("White", board)

    def test_has_any_legal_moves_exact_one_move(self, monkeypatch):
        """
        Patch legal_move so that exactly one move is legal.
        Ensures the function returns True as soon as any legal move exists.
        """
        board = initialise_board()

        def only_one(colour, coord, board_arg):
            return coord == (3, 4)

        # same as above test
        monkeypatch.setattr("components.legal_move", only_one)

        assert has_any_legal_moves("Black", board)
        assert has_any_legal_moves("White", board)


class TestCountPieces:
    """Tests for piece counting."""

    def test_count_pieces_initial_position(self):
        """Basic count on initial board."""
        board = initialise_board()
        black, white = count_pieces(board)
        assert black == 2
        assert white == 2

    def test_count_pieces_empty_board(self):
        """Empty board returns (0, 0)."""
        size = 8
        board = [[EMPTY for _ in range(size)] for _ in range(size)]
        black, white = count_pieces(board)
        assert black == 0
        assert white == 0

    def test_count_pieces_custom_board_mixed(self):
        """Small manual setup."""
        board = [
            [BLACK, WHITE, EMPTY],
            [WHITE, BLACK, EMPTY],
            [BLACK, EMPTY, WHITE],
        ]

        black, white = count_pieces(board)

        assert black == 3
        assert white == 3

    def test_count_pieces_after_manual_updates(self):
        """Counts should reflect manual edits."""
        board = initialise_board()

        board[0][0] = BLACK
        board[7][7] = BLACK

        board[0][7] = WHITE
        board[7][0] = WHITE

        black, white = count_pieces(board)

        assert black == 4
        assert white == 4
