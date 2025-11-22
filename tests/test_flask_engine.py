"""Tests for flask_engine.py"""

import io
import json
import os
import sys
import copy

# ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask_engine import (
    app,
    game_state,
    new_game,
    is_game_finished,
)
from components import (
    initialise_board,
)


class TestNewGame:
    """Testing creating a new game."""

    def test_new_game_sets_initial_state(self):
        """new_game should set up a fresh initial game state."""
        # mess with the game_state first to be sure it gets reset
        game_state.clear()
        game_state.update(
            {
                "board": [["junk"]],
                "current": "White",
                "move_history": ["A1"],
                "finished": True,
                "random_extra_key": 123,
            }
        )

        new_game()

        # basic keys
        assert "board" in game_state
        assert "current" in game_state
        assert "move_history" in game_state
        assert "game_finished" in game_state

        # values
        assert game_state["current"] == "Black"
        assert game_state["move_history"] == []
        assert not game_state["game_finished"]

        # board should be the standard initial board
        expected_board = initialise_board()
        assert game_state["board"] == expected_board

        # extra keys should be gone because of clear() + update()
        assert "random_extra_key" not in game_state


    def test_new_game_is_idempotent(self):
        """Calling new_game twice should always give a clean fresh state."""
        # first call
        new_game()
        first_board = copy.deepcopy(game_state["board"])
        first_current = game_state["current"]
        first_history = list(game_state["move_history"])
        first_game_finished = game_state["game_finished"]

        # mess with state
        game_state["current"] = "White"
        game_state["move_history"].append("D3")
        game_state["finished"] = True

        # second call
        new_game()

        # after second call, it should look like a fresh game again
        assert game_state["board"] == first_board
        assert game_state["current"] == first_current
        assert game_state["move_history"] == first_history
        assert game_state["game_finished"] == first_game_finished


    def test_new_game_creates_new_board_object(self):
        """new_game should create a new board object, not reuse an old reference."""
        new_game()
        board_before = game_state["board"]

        # Call again
        new_game()
        board_after = game_state["board"]

        # they should be equal in content but not the same object
        assert board_before == board_after
        assert board_before is not board_after


class TestIsGameFinished:
    """Tests for checking if the game is finished or not."""

    def test_is_game_finished_no_moves_for_either_player(self, monkeypatch):
        """
        Game should be finished Black and White don't have any legal moves.
        """

        calls = []

        def fake_has_any_legal_moves(colour, board):
            # record call order just to be sure both colours are checked
            calls.append(colour)
            return False  # no one has any moves

        monkeypatch.setattr("flask_engine.has_any_legal_moves", fake_has_any_legal_moves)

        dummy_board = [["." for _ in range(8)] for _ in range(8)]

        result = is_game_finished(dummy_board)

        assert result is True
        # ensure both colours were queried
        assert calls == ["Black", "White"]

    def test_is_game_finished_black_has_moves(self, monkeypatch):
        """
        Game should not be finished if Black has at least one legal move.
        """

        def fake_has_any_legal_moves(colour, board):
            if colour == "Black":
                return True
            return False

        monkeypatch.setattr("flask_engine.has_any_legal_moves", fake_has_any_legal_moves)

        dummy_board = [["." for _ in range(8)] for _ in range(8)]

        result = is_game_finished(dummy_board)

        assert result is False

    def test_is_game_finished_full_board(self):
        """
        Game should be finished for a full board
        """

        dummy_board = [["W" for _ in range(8)] for _ in range(8)]
        result = is_game_finished(dummy_board)

        assert result is True

    def test_is_game_finished_real_position(self):
        """
        Game should be finished for this position
        this is actually the position that arises after the fastest
        sequence of moves for a player in Othello
        """

        dummy_board = [["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "],
                       ["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "],
                       ["None ", "None ", "None ", "None ", "Black", "None ", "None ", "None "],
                       ["None ", "None ", "None ", "Black", "Black", "Black", "None ", "None "],
                       ["None ", "None ", "Black", "Black", "Black", "Black", "Black", "None "],
                       ["None ", "None ", "None ", "Black", "Black", "Black", "None ", "None "],
                       ["None ", "None ", "None ", "None ", "Black", "None ", "None ", "None "],
                       ["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "]]
        result = is_game_finished(dummy_board)

        assert result is True


class TestLoad:
    """Tests for loading a game."""

    def setup_method(self):
        """Create a fresh test client and reset game before each test."""
        self.client = app.test_client()
        new_game()

    def test_load_success(self, monkeypatch):
        """
        If savegame.json exists and contains a valid game_state,
        /load should return success and update the global game_state.
        """

        # same as current, but with game_finished changed
        fake_loaded_state = dict(game_state)
        fake_loaded_state["game_finished"] = True  # will be recomputed in /load

        # fake open that returns a dummy context manager
        class DummyFile:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_open(*args, **kwargs):
            return DummyFile()

        # patch builtins.open so no real file access happens
        monkeypatch.setattr("builtins.open", fake_open)

        # patch json.load inside flask_engine to return our fake state
        def fake_json_load(_file_obj):
            return fake_loaded_state

        monkeypatch.setattr("flask_engine.json.load", fake_json_load)

        resp = self.client.get("/load")
        data = resp.get_json()

        assert data["status"] == "success"
        assert "Game loaded" in data["message"]

        # game_state should now match what we "loaded" (except for recomputed game_finished)
        assert game_state["board"] == fake_loaded_state["board"]
        assert game_state["current"] == fake_loaded_state["current"]
        assert game_state["move_history"] == fake_loaded_state["move_history"]

        # load() recomputes game_finished via is_game_finished,
        # so from the starting position it should be False.
        assert not game_state["game_finished"]

    def test_load_no_file_starts_new_game(self, monkeypatch):
        """
        If savegame.json does not exist , /load should return fail and start a new game.
        """
        game_state["board"] = [["Black" for i in range(8)] for i in range(8)]
        game_state["current"] = "White"
        game_state["game_finished"] = True
        game_state["move_history"] = ["A1"]

        def fake_open(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("builtins.open", fake_open)

        resp = self.client.get("/load")
        data = resp.get_json()

        assert data["status"] == "fail"
        assert "No save file found" in data["message"]

        # /load calls new_game() so we should have a fresh game
        assert game_state["current"] == "Black"
        assert game_state["game_finished"] is False
        assert "board" in game_state
        assert isinstance(game_state["move_history"], list)


class TestMove:
    """Tests for moving"""
    def setup_method(self):
        """Create a fresh test client and reset game before each test."""
        self.client = app.test_client()
        new_game()

    def test_move_invalid_coordinates_non_numeric(self):
        """Non-numeric x or y should return a fail status and error message."""
        resp = self.client.get("/move?x=ooga&y=3")
        data = resp.get_json()

        assert data["status"] == "fail"
        assert "Invalid coordinates" in data["message"]
        # board and current player should still be present
        assert "board" in data
        assert "current_player" in data

    def test_move_invalid_coordinates_missing(self):
        """Missing x or y should also be treated as invalid coordinates."""
        resp = self.client.get("/move?x=&y=")
        data = resp.get_json()

        assert data["status"] == "fail"
        assert "Invalid coordinates" in data["message"]

    def test_move_illegal_from_start(self):
        """
        From the initial position, (1,1) / 'A1' is illegal.
        The endpoint should respond with fail and not change the current player.
        """
        # check that current player is Black after new_game()
        assert game_state["current"] == "Black"

        resp = self.client.get("/move?x=1&y=1")  # A1
        data = resp.get_json()

        assert data["status"] == "fail"
        assert "illegal move" in data["message"]
        # current player stays Black
        assert data["current_player"] == "Black"
        # no notation / finished info in fail case
        assert "notation" not in data
        assert "finished" not in data

    def test_move_legal_opening(self):
        """
        A legal opening move, Black plays C4 (3,4).
        Should work, flip at one disc, and switch player to White,
        and add notation to move history.
        """
        resp = self.client.get("/move?x=3&y=4")  # C4
        data = resp.get_json()

        assert data["status"] == "success"
        # notation should be "C4"
        assert data["notation"] == "C4"
        assert "Black played C4" in data["message"]

        # current player should now be White
        assert data["current_player"] == "White"

        # finished should be None (game continues)
        assert data["finished"] is None

        # global game_state should have move history with C4 now
        assert "C4" in game_state["move_history"]

    def test_move_when_game_already_finished(self):
        """
        If game_state['game_finished'] is True, /move should not try to
        apply a move and should return a 'game already over' message.
        """
        # set game as finished before the move
        game_state["game_finished"] = True
        game_state["current"] = "Black"

        resp = self.client.get("/move?x=3&y=4")
        data = resp.get_json()

        assert data["status"] == "success"
        assert "already over" in data["message"]

    def test_move_that_results_in_game_over(self, monkeypatch):
        """
        Force a scenario where, after a legal move, neither player
        has any legal moves, so the game should end and 'finished'
        text should be included.
        """

        # allow exactly one move to be legal: (3,4) for the current player.
        def fake_legal_move(colour, coord, board):
            return coord == (3, 4)

        # after any move, pretend there are no legal moves for either side.
        def fake_has_any_legal_moves(colour, board):
            return False

        # patch functions inside the flask_engine module (where they're looked up).
        monkeypatch.setattr("flask_engine.legal_move", fake_legal_move)
        monkeypatch.setattr("flask_engine.has_any_legal_moves", fake_has_any_legal_moves)

        # we still want apply_move to run so the notation and flip logic works,
        # so we don't patch it here.

        resp = self.client.get("/move?x=3&y=4")  # C4
        data = resp.get_json()

        assert data["status"] == "success"
        assert data["notation"] == "C4"

        # because fake_has_any_legal_moves returns False for both colours,
        # is_game_finished will mark the game finished and send final text.
        assert data["finished"] is not None
        assert "Game Over!" in data["finished"]

        # game_state finished flag should also be True
        assert game_state["game_finished"] is True

    def test_move_that_results_in_game_over_real(self):
        """
        Force a real scenario where, after a legal move, neither player
        has any legal moves, so the game should end and 'finished'
        text should be included.

        Position is from fastest game possible.
        """

        game_state["board"] = [
            ["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "],
            ["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "],
            ["None ", "None ", "None ", "None ", "Black", "None ", "None ", "None "],
            ["None ", "None ", "None ", "White", "Black", "Black", "None ", "None "],
            ["None ", "None ", "None ", "White", "White", "White", "Black", "None "],
            ["None ", "None ", "None ", "White", "Black", "Black", "None ", "None "],
            ["None ", "None ", "None ", "None ", "Black", "None ", "None ", "None "],
            ["None ", "None ", "None ", "None ", "None ", "None ", "None ", "None "],
        ]

        game_state["current"] = "Black"
        game_state["move_history"] = ["E6", "F4", "E3", "F6", "G5", "D6", "E7", "F5"]
        game_state["game_finished"] = False

        # black plays C5
        resp = self.client.get("/move?x=3&y=5") # (3,5)
        data = resp.get_json()

        assert data["status"] == "success"
        assert data["notation"] == "C5"
        assert data["finished"] is not None
        assert "Game Over!" in data["finished"]
        assert game_state["game_finished"] is True
