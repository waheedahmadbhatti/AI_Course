
import tkinter as tk
from tkinter import messagebox


# ==========================================
# TIC-TAC-TOE GAME
# ==========================================

# Current player
current_player = "X"

# Store the game board
board = [""] * 9


# ==========================================
# COLORS
# ==========================================

BG_COLOR = "#121826"
CARD_COLOR = "#1B2435"
BOARD_COLOR = "#202B3F"

X_COLOR = "#38BDF8"
O_COLOR = "#FB7185"

TEXT_COLOR = "#FFFFFF"
SECONDARY_TEXT = "#94A3B8"

BUTTON_COLOR = "#273449"
BUTTON_HOVER = "#33445D"

NEW_GAME_COLOR = "#2563EB"
NEW_GAME_HOVER = "#3B82F6"

EXIT_COLOR = "#DC2626"
EXIT_HOVER = "#EF4444"


# ==========================================
# CHECK WINNER
# ==========================================

def check_winner():

    # All possible winning combinations
    winning_combinations = [
        (0, 1, 2),  # Top row
        (3, 4, 5),  # Middle row
        (6, 7, 8),  # Bottom row
        (0, 3, 6),  # Left column
        (1, 4, 7),  # Middle column
        (2, 5, 8),  # Right column
        (0, 4, 8),  # Diagonal
        (2, 4, 6)   # Diagonal
    ]

    # Check every winning combination
    for a, b, c in winning_combinations:

        if board[a] != "" and board[a] == board[b] == board[c]:
            return board[a]

    # Check for draw
    if "" not in board:
        return "Draw"

    # Game is still running
    return None


# ==========================================
# BUTTON HOVER EFFECT
# ==========================================

def button_enter(event):

    # Only change color if button is empty
    if event.widget["text"] == "":
        event.widget.config(bg=BUTTON_HOVER)


def button_leave(event):

    # Only change color if button is empty
    if event.widget["text"] == "":
        event.widget.config(bg=BUTTON_COLOR)


# ==========================================
# BUTTON CLICK
# ==========================================

def button_click(index):

    global current_player

    # IMPORTANT:
    # Don't allow player to change an already
    # selected box
    if board[index] != "":
        return

    # Put X or O on the board
    board[index] = current_player

    # Display X or O on the button
    buttons[index].config(
        text=current_player,
        fg=X_COLOR if current_player == "X" else O_COLOR,
        bg=BOARD_COLOR
    )

    # Check if somebody won
    result = check_winner()

    if result == "X":
        messagebox.showinfo(
            "Game Over",
            "Player X Wins! 🎉"
        )
        reset_game()
        return

    elif result == "O":
        messagebox.showinfo(
            "Game Over",
            "Player O Wins! 🎉"
        )
        reset_game()
        return

    elif result == "Draw":
        messagebox.showinfo(
            "Game Over",
            "It's a Draw! 🤝"
        )
        reset_game()
        return

    # Switch player
    if current_player == "X":
        current_player = "O"
    else:
        current_player = "X"

    # Update player label
    player_label.config(
        text=f"Player {current_player}'s Turn",
        fg=X_COLOR if current_player == "X" else O_COLOR
    )


# ==========================================
# RESET GAME
# ==========================================

def reset_game():

    global current_player

    # Reset board
    board.clear()
    board.extend([""] * 9)

    # Start again with X
    current_player = "X"

    # Clear all buttons
    for button in buttons:
        button.config(
            text="",
            fg=TEXT_COLOR,
            bg=BUTTON_COLOR
        )

    # Update label
    player_label.config(
        text="Player X's Turn",
        fg=X_COLOR
    )


# ==========================================
# MAIN WINDOW
# ==========================================

root = tk.Tk()

root.title("Tic-Tac-Toe")

root.geometry("500x650")

root.resizable(False, False)

# Background
root.configure(bg=BG_COLOR)


# ==========================================
# TITLE
# ==========================================

title_label = tk.Label(
    root,
    text="TIC-TAC-TOE",
    font=("Arial", 30, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
)

title_label.pack(pady=(25, 5))


# Subtitle
subtitle_label = tk.Label(
    root,
    text="Classic game • Two players",
    font=("Arial", 11),
    bg=BG_COLOR,
    fg=SECONDARY_TEXT
)

subtitle_label.pack(pady=(0, 20))


# ==========================================
# PLAYER CARD
# ==========================================

player_card = tk.Frame(
    root,
    bg=CARD_COLOR,
    padx=30,
    pady=12
)

player_card.pack(pady=5)


player_label = tk.Label(
    player_card,
    text="Player X's Turn",
    font=("Arial", 17, "bold"),
    bg=CARD_COLOR,
    fg=X_COLOR
)

player_label.pack()


# ==========================================
# GAME BOARD CARD
# ==========================================

board_card = tk.Frame(
    root,
    bg=BOARD_COLOR,
    padx=15,
    pady=15
)

board_card.pack(pady=25)


# ==========================================
# GAME BOARD
# ==========================================

game_frame = tk.Frame(
    board_card,
    bg=BOARD_COLOR
)

game_frame.pack()


# Store buttons
buttons = []


# ==========================================
# CREATE 9 BUTTONS
# ==========================================

for i in range(9):

    button = tk.Button(
        game_frame,
        text="",
        font=("Arial", 28, "bold"),
        width=5,
        height=2,

        # Colors
        bg=BUTTON_COLOR,
        fg=TEXT_COLOR,
        activebackground=BUTTON_HOVER,
        activeforeground=TEXT_COLOR,

        # Remove traditional button border
        relief="flat",
        bd=0,

        # Cursor
        cursor="hand2",

        # Game functionality
        command=lambda index=i: button_click(index)
    )

    # Arrange buttons in 3x3 grid
    button.grid(
        row=i // 3,
        column=i % 3,
        padx=6,
        pady=6
    )

    # Hover effects
    button.bind("<Enter>", button_enter)
    button.bind("<Leave>", button_leave)

    buttons.append(button)


# ==========================================
# BUTTONS FRAME
# ==========================================

control_frame = tk.Frame(
    root,
    bg=BG_COLOR
)

control_frame.pack(pady=10)


# ==========================================
# NEW GAME BUTTON
# ==========================================

reset_button = tk.Button(
    control_frame,
    text="↻  New Game",
    font=("Arial", 13, "bold"),

    width=15,

    bg=NEW_GAME_COLOR,
    fg="white",

    activebackground=NEW_GAME_HOVER,
    activeforeground="white",

    relief="flat",
    bd=0,

    cursor="hand2",

    command=reset_game
)

reset_button.grid(
    row=0,
    column=0,
    padx=8
)


# ==========================================
# EXIT BUTTON
# ==========================================

exit_button = tk.Button(
    control_frame,
    text="✕  Exit",
    font=("Arial", 13, "bold"),

    width=10,

    bg=EXIT_COLOR,
    fg="white",

    activebackground=EXIT_HOVER,
    activeforeground="white",

    relief="flat",
    bd=0,

    cursor="hand2",

    command=root.destroy
)

exit_button.grid(
    row=0,
    column=1,
    padx=8
)


# ==========================================
# FOOTER
# ==========================================

footer_label = tk.Label(
    root,
    text="Have fun playing! 🎮",
    font=("Arial", 10),
    bg=BG_COLOR,
    fg=SECONDARY_TEXT
)

footer_label.pack(
    pady=(20, 0)
)


# ==========================================
# START GAME
# ==========================================

root.mainloop()

