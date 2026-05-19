import tkinter as tk
from tkinter import messagebox as mb
from tkinter import font

MAIN_WINDOW_WIDTH = 400
MAIN_WINDOW_HEIGHT = 400

GAME_WIDTH = 600
GAME_HEIGHT = 605

BOARD_SIZE = 3

root = tk.Tk()
root.title("Tic Tac Toe")
root.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}")
GAME_FONT = font.Font(family="Comic Sans MS", size=15)

turn = "X"
mode = None   # AI or 2-player
buttons = []  # board buttons
game_win = None
turn_label = None


# ---------------- WIN CHECKER ---------------- #

def check_win(board):
    size = len(board)
    b = [[btn["text"] for btn in row] for row in board]

    # Rows
    for row in b:
        if row.count(row[0]) == size and row[0] != "":
            return row[0]

    # Columns
    for c in range(size):
        col = [b[r][c] for r in range(size)]
        if col.count(col[0]) == size and col[0] != "":
            return col[0]

    # Diagonals
    diag1 = [b[i][i] for i in range(size)]
    if diag1.count(diag1[0]) == size and diag1[0] != "":
        return diag1[0]

    diag2 = [b[i][size - 1 - i] for i in range(size)]
    if diag2.count(diag2[0]) == size and diag2[0] != "":
        return diag2[0]

    # Draw
    if all(b[r][c] != "" for r in range(size) for c in range(size)):
        return "Draw!"

    return None


# ---------------- MINIMAX ---------------- #

def minimax(board, depth, is_ai_turn, ai_symbol, human_symbol):
    result = check_win(board)

    if result == ai_symbol:
        return 1
    if result == human_symbol:
        return -1
    if result == "Draw!":
        return 0

    size = len(board)

    if is_ai_turn:
        best_score = -999999
        for r in range(size):
            for c in range(size):
                if board[r][c]["text"] == "":
                    board[r][c]["text"] = ai_symbol
                    score = minimax(board, depth + 1, False, ai_symbol, human_symbol)
                    board[r][c]["text"] = ""
                    best_score = max(best_score, score)
        return best_score

    else:
        worst_score = 999999
        for r in range(size):
            for c in range(size):
                if board[r][c]["text"] == "":
                    board[r][c]["text"] = human_symbol
                    score = minimax(board, depth + 1, True, ai_symbol, human_symbol)
                    board[r][c]["text"] = ""
                    worst_score = min(worst_score, score)
        return worst_score


# ---------------- BEST MOVE ---------------- #

def best_move(board, ai_symbol, human_symbol):
    size = len(board)
    best_score = -999999
    move = None

    for r in range(size):
        for c in range(size):
            if board[r][c]["text"] == "":
                board[r][c]["text"] = ai_symbol
                score = minimax(board, 0, False, ai_symbol, human_symbol)
                board[r][c]["text"] = ""

                if score > best_score:
                    best_score = score
                    move = (r, c)

    return move


# ---------------- GAME RESET ---------------- #

def reset_board():
    global turn
    turn = "X"
    turn_label.config(text="X turn...")

    for row in buttons:
        for btn in row:
            btn.config(text="")


# ---------------- UPDATE FUNCTION ---------------- #

def update(btn, value):
    global turn

    if btn["text"] != "":
        mb.showerror("Invalid Move", "This cell is already occupied!")
        return

    # Human move
    btn.config(text=value)

    result = check_win(buttons)
    if result:
        turn_label.config(text=f"{result} wins!" if result in ["X", "O"] else "Draw!")
        root.after(2000, reset_board)
        return

    # Switch turn
    turn = "O" if turn == "X" else "X"
    turn_label.config(text=f"{turn} turn...")

    # AI move
    if mode == "AI" and turn == "O":
        r, c = best_move(buttons, "O", "X")
        buttons[r][c].config(text="O")

        result = check_win(buttons)
        if result:
            turn_label.config(text=f"{result} wins!" if result in ["X", "O"] else "Draw!")
            root.after(2000, reset_board)
            return

        turn = "X"
        turn_label.config(text="X turn...")


# ---------------- GAME WINDOW ---------------- #

def start_game(selected_mode):
    global mode, game_win, turn_label, buttons

    mode = selected_mode

    game_win = tk.Toplevel(root)
    game_win.title("Tic Tac Toe")
    game_win.geometry(f"{GAME_WIDTH}x{GAME_HEIGHT}")

    turn_label = tk.Label(game_win, text="X turn...", font=GAME_FONT)
    turn_label.grid(row=0, column=0, columnspan=3)

    buttons = [[] for _ in range(BOARD_SIZE)]

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            btn = tk.Button(game_win, text="", font=GAME_FONT, width=15, height=5)
            btn.grid(row=r+1, column=c, padx=5, pady=5)
            btn.config(command=lambda rr=r, cc=c: update(buttons[rr][cc], turn))
            buttons[r].append(btn)


# ---------------- MODE SELECTION SCREEN ---------------- #

def mode_screen():
    label = tk.Label(root, text="Choose Game Mode", font=GAME_FONT)
    label.pack(pady=20)

    ai_btn = tk.Button(root, text="Play vs AI", font=GAME_FONT, width=20,
                       command=lambda: start_game("AI"))
    ai_btn.pack(pady=10)

    two_btn = tk.Button(root, text="2 Player Mode", font=GAME_FONT, width=20,
                        command=lambda: start_game("2P"))
    two_btn.pack(pady=10)


mode_screen()
root.mainloop()
