"""Flask web interface for the Othello game."""

import json

from flask import Flask, render_template, request, jsonify

from components import (
    initialise_board,
    legal_move,
    apply_move,
    count_pieces,
    has_any_legal_moves
)

app = Flask(__name__)

# single dict to hold all game state
game_state: dict = {}


def new_game():
    """Initialise a fresh game."""
    board = initialise_board()

    game_state.clear()
    game_state.update(
        {
            "board": board,
            "current": "Black",
            "move_history": [],
            "game_finished": False,
        }
    )


def is_game_finished(board):
    """Return True if the game is finished based on legal moves."""
    # Game ends when neither player has a legal move
    if not has_any_legal_moves("Black", board) and not has_any_legal_moves(
        "White", board
    ):
        return True
    return False


def other_colour(colour):
    """Return the opposite colour."""
    return "White" if colour == "Black" else "Black"


def coord_to_notation(x, y):
    """Convert numeric (x, y) to notation like 'D3'."""
    letter = chr(ord("A") + x - 1)
    return f"{letter}{y}"


@app.route("/")
def index():
    """Render the main board page."""
    print("Indexing")

    if not game_state:
        new_game()

    return render_template(
        "Othello Board.html",
        game_board=game_state["board"],
        current_player=game_state["current"],
        move_history=game_state.get("move_history", []),
        finished=game_state.get("game_finished", False),
    )


@app.route("/move")
def move():
    """Handle a move sent from the HTML/JS via ?x=&y= query params."""
    if not game_state:
        new_game()

    # read x and y from query parameters (1-based)
    try:
        x = int(request.args.get("x", ""))
        y = int(request.args.get("y", ""))
    except ValueError:
        # invalid or missing coordinates - shouldn't happen in practice
        return jsonify(
            {
                "status": "fail",
                "message": "Invalid coordinates.",
                "board": game_state["board"],
                "current_player": game_state.get("current", "Black"),
            }
        )

    board = game_state["board"]
    current = game_state["current"]

    # if the game is already finished, do NOT try the move or send final score popup
    if game_state.get("game_finished", False):
        return jsonify(
            {
                "status": "success",
                "message": "The game is already over. Click 'Restart game' to play a new match!",
                "board": board,
                "current_player": current,
            }
        )

    # if move is not legal, return a message
    if not legal_move(current, (x, y), board):
        attempted = coord_to_notation(x, y)
        return jsonify(
            {
                "status": "fail",
                "message": f"{current} attempted {attempted}, illegal move.",
                "board": board,
                "current_player": current,
            }
        )

    # apply the move and count flipped discs
    flips = apply_move(current, (x, y), board)

    # notation like "D3"
    notation = coord_to_notation(x, y)
    game_state["move_history"].append(notation)

    # build success message
    flip_word = "disc" if flips == 1 else "discs"
    message = f"{current} played {notation}, {flips} {flip_word} flipped."

    # pass handling logic
    opponent = other_colour(current)
    pass_info = ""

    if has_any_legal_moves(opponent, board):
        # normal case: opponent can move
        next_player = opponent
    elif has_any_legal_moves(current, board):
        # opponent has no legal moves, current player moves again (pass)
        next_player = current
        pass_info = f" {opponent} has no legal moves, so {current} plays again."
    else:
        # neither player has a legal move, game will be finished
        next_player = opponent  # doesn't really matter now

    game_state["current"] = next_player

    # check if the game is finished
    finished_text = None
    if is_game_finished(board):
        game_state["game_finished"] = True

        black, white = count_pieces(board)
        if black > white:
            winner = "Black wins!"
        elif white > black:
            winner = "White wins!"
        else:
            winner = "It's a draw!"
        finished_text = (
            f"Game Over! Final Score — Black: {black}, White: {white}. {winner}"
        )

    # append any pass info to the base message
    message += pass_info

    # normal response if game is not finished
    if finished_text is None:
        return jsonify(
            {
                "status": "success",
                "message": message,
                "board": board,
                "current_player": next_player,
                "notation": notation,
                "finished": None,
            }
        )
    # final response if game ended
    return jsonify(
        {
            "status": "success",
            "message": message,
            "board": board,
            "current_player": game_state["current"],
            "notation": notation,
            "finished": finished_text,
        }
    )


@app.route("/save")
def save():
    """Save the current game_state to a JSON file."""
    if not game_state:
        new_game()

    with open("savegame.json", "w", encoding="utf-8") as save_file:
        json.dump(game_state, save_file)
    return jsonify({"status": "success", "message": "Game saved."})


@app.route("/load")
def load():
    """Load game_state from a JSON file (if it exists)."""
    try:
        with open("savegame.json", "r", encoding="utf-8") as save_file:
            loaded_state = json.load(save_file)

        game_state.clear()
        game_state.update(loaded_state)

        board = game_state["board"]

        # recompute finished state from the loaded position
        game_state["game_finished"] = is_game_finished(board)

        return jsonify({"status": "success", "message": "Game loaded."})

    except FileNotFoundError:
        new_game()
        return jsonify(
            {
                "status": "fail",
                "message": "No save file found. A new game has been started.",
            }
        )


@app.route("/restart")
def restart():
    """Restart the entire game to the initial state."""
    new_game()
    return jsonify({"status": "success", "message": "Game restarted."})


if __name__ == "__main__":
    print("Starting Othello")
    new_game()
    app.run(debug=True)
