"""Command-line game engine for Othello."""

from components import (
    initialise_board,
    print_board,
    legal_move,
    apply_move,
    count_pieces,
    has_any_legal_moves,
)


def parse_letter_number_input(raw):
    """
    Parse moves like:
    'A 3', 'd 6', 'H8', 'c4'
    Returns (x, y) as numbers 1–8.
    """
    raw = raw.strip().replace(",", "").replace(" ", "")
    raw = raw.upper()

    if len(raw) < 2:
        raise ValueError("Input must contain a letter and a number.")

    # first character must be a letter between a–h
    letter = raw[0]
    if not "A" <= letter <= "H":
        raise ValueError("Column must be a letter from A to H.")

    # convert letter to column number (a = 1, b = 2, etc.)
    x = ord(letter) - ord("A") + 1

    # remaining characters must form a valid row number 1–8
    try:
        y = int(raw[1:])
    except ValueError as exc:
        raise ValueError("Row must be a number between 1 and 8.") from exc

    if not 1 <= y <= 8:
        raise ValueError("Row must be between 1 and 8.")

    return (x, y)


def cli_coords_input():
    """Ask the user until a valid move is entered or they quit."""
    while True:
        raw = input("Enter your move like 'A 6' or 'd7', or 'q' to quit: ").strip()

        if raw.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            raise SystemExit

        try:
            return parse_letter_number_input(raw)
        except ValueError:
            print("Invalid input. Examples: 'A 6', 'd7', 'H8'")


def other_colour(colour):
    """Return the opposite colour name."""
    return "White" if colour == "Black" else "Black"


def simple_game_loop():
    """Run a simple command-line game loop for Othello."""
    print("Welcome to Othello")
    print("Black moves first!\n")

    board = initialise_board()
    current = "Black"
    moves_remaining = 60

    while moves_remaining > 0:
        print_board(board)
        print()

        if not has_any_legal_moves(current, board):
            opponent = other_colour(current)
            if not has_any_legal_moves(opponent, board):
                print(f"{current} has no legal moves.")
                print(f"{opponent} has no legal moves.")
                break
            print(f"{current} has no legal moves and passes.")
            current = opponent

        print(f"{current}'s turn!")

        while True:
            coord = cli_coords_input()
            if not legal_move(current, coord, board):
                print("Illegal move, please try again.")
                continue
            flips = apply_move(current, coord, board)
            print(f"Move applied - {flips} discs flipped.")
            moves_remaining -= 1
            break

        if moves_remaining == 0:
            break

        current = other_colour(current)
        print()

    print()
    print_board(board)
    print("\nGame over!")

    black, white = count_pieces(board)
    print(f"Black: {black}, White: {white}")

    if black > white:
        print("Black wins!")
    elif white > black:
        print("White wins!")
    else:
        print("It's a draw!")


if __name__ == "__main__":
    simple_game_loop()
