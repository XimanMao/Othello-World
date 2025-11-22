"""Components of the Othello game"""

BOARD_SIZE_DEFAULT = 8

EMPTY = "None "
BLACK = "Black"
WHITE = "White"

DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


def initialise_board(size: int = BOARD_SIZE_DEFAULT):
    """
    Creates an Othello board with the standard starting layout.
    White at (4,4) and (5,5)
    Black at (4,5) and (5,4)
    """
    # middle two indices (3 and 4 for 8x8 board)
    board = [[EMPTY for _ in range(size)] for _ in range(size)]
    mid1, mid2 = size // 2 - 1, size // 2

    board[mid1][mid1] = WHITE
    board[mid2][mid2] = WHITE
    board[mid1][mid2] = BLACK
    board[mid2][mid1] = BLACK

    return board


def print_board(board):
    """Print an ASCII representation of the board to the console."""
    size = len(board)

    # print each row (numbers on the left)
    for y in range(size):
        row_display = []
        for x in range(size):
            val = board[y][x].strip()
            if val == "None":
                ch = "."
            elif val == "Black":
                ch = "B"
            elif val == "White":
                ch = "W"
            else:
                ch = "?"
            row_display.append(f"{ch:2}")

        # row number on the left
        print(f"{y + 1:2} | " + " ".join(row_display))

    print("    " + "-" * (size * 3 - 1))

    # bottom letters A–H
    letters = " ".join(f" {chr(ord('A') + i)}" for i in range(size))
    print("    " + letters)

def has_any_legal_moves(colour, board):
    """Check if the given colour has at least one legal move."""
    size = len(board)
    for y in range(1, size + 1):
        for x in range(1, size + 1):
            if legal_move(colour, (x, y), board):
                return True
    return False

def _discs_to_flip(board, colour: str, x0: int, y0: int):
    """Return list of discs that would be flipped if colour played at (x0,y0)."""
    size = len(board)

    if not (0 <= x0 < size and 0 <= y0 < size): # out of bounds moves
        return []

    if board[y0][x0].strip() != "None": # moves on occupied squares
        return []

    # determine the player and opponent's colours
    me = colour.strip()
    if me not in ("Black", "White"):
        return []

    other = "White" if me == "Black" else "Black"
    flips = []

    # check each of the 8 directions
    for dx, dy in DIRECTIONS:
        cx, cy = x0 + dx, y0 + dy
        line = [] # store opponent tiles along this direction

        # walk along this direction
        while 0 <= cx < size and 0 <= cy < size:
            cell = board[cy][cx].strip()

            if cell == other: # opponent's tile
                line.append((cx, cy))
            elif cell == me:
                if line: # player's tile
                    flips.extend(line)
                break
            else: # empty tile means line is broken
                break
            cx += dx
            cy += dy
    return flips


def legal_move(colour: str, coord: tuple, board) -> bool:
    """Return True if placing 'colour' at coord is legal."""
    x, y = coord
    x0, y0 = x - 1, y - 1 # convert to indexing starting from 0

    # check if move is on the board
    if not (0 <= x0 < len(board) and 0 <= y0 < len(board)):
        return False

    return len(_discs_to_flip(board, colour, x0, y0)) > 0


def apply_move(colour: str, coord: tuple, board):
    """Apply a legal move and flip discs."""
    x, y = coord
    x0, y0 = x - 1, y - 1

    flips = _discs_to_flip(board, colour, x0, y0)
    # if not flips:
    #     return 0

    piece = BLACK if colour == "Black" else WHITE
    board[y0][x0] = piece
    for fx, fy in flips:
        board[fy][fx] = piece
    return len(flips)


def count_pieces(board):
    """Count black and white pieces."""
    black = white = 0
    for row in board:
        for cell in row:
            v = cell.strip()
            if v == "Black":
                black += 1
            elif v == "White":
                white += 1
    return black, white
