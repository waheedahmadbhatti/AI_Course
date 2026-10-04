
import tkinter as tk
from tkinter import messagebox


# ==========================================
# PASSWORD MANAGER
# ==========================================


# Function to read the saved password
def get_password():

    try:
        with open("password.txt", "r") as f:
            return f.read().strip()

    except FileNotFoundError:
        return ""


# ==========================================
# PASSWORD VALIDATION
# ==========================================

def validate_password(password):

    # IMPORTANT: Check password length
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    # IMPORTANT: Check for uppercase letter
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."

    # IMPORTANT: Check for special character
    if not any(not char.isalnum() for char in password):
        return "Password must contain at least one special character."

    # Password is valid
    return ""


# ==========================================
# SET NEW PASSWORD
# ==========================================

def set_password():

    new_password = new_password_entry.get()
    confirm_password = confirm_password_entry.get()

    # Check if fields are empty
    if not new_password or not confirm_password:
        messagebox.showerror(
            "Error",
            "Please enter and confirm your password."
        )
        return

    # IMPORTANT: Validate password
    error = validate_password(new_password)

    if error:
        messagebox.showerror("Invalid Password", error)
        return

    # IMPORTANT: Check whether passwords match
    if new_password != confirm_password:
        messagebox.showerror(
            "Error",
            "Passwords do not match!"
        )
        return

    # Save password
    with open("password.txt", "w") as f:
        f.write(new_password)

    messagebox.showinfo(
        "Success",
        "Password set successfully!"
    )

    # Clear fields
    new_password_entry.delete(0, tk.END)
    confirm_password_entry.delete(0, tk.END)


# ==========================================
# CHANGE PASSWORD
# ==========================================

def change_password():

    password = get_password()

    # Check if password exists
    if not password:
        messagebox.showerror(
            "Error",
            "No password has been set yet."
        )
        return

    old_password = old_password_entry.get()
    new_password = change_new_password_entry.get()
    confirm_password = change_confirm_password_entry.get()

    # Check empty fields
    if not old_password or not new_password or not confirm_password:
        messagebox.showerror(
            "Error",
            "Please fill all fields."
        )
        return

    # IMPORTANT: Verify old password
    if old_password != password:
        messagebox.showerror(
            "Error",
            "Incorrect old password!"
        )
        return

    # IMPORTANT: Validate new password
    error = validate_password(new_password)

    if error:
        messagebox.showerror(
            "Invalid Password",
            error
        )
        return

    # IMPORTANT: Check confirmation
    if new_password != confirm_password:
        messagebox.showerror(
            "Error",
            "Passwords do not match!"
        )
        return

    # Save new password
    with open("password.txt", "w") as f:
        f.write(new_password)

    messagebox.showinfo(
        "Success",
        "Password changed successfully!"
    )

    # Clear fields
    old_password_entry.delete(0, tk.END)
    change_new_password_entry.delete(0, tk.END)
    change_confirm_password_entry.delete(0, tk.END)


# ==========================================
# CHECK PASSWORD
# ==========================================

def check_password():

    password = get_password()

    # Check whether password exists
    if not password:
        messagebox.showerror(
            "Error",
            "No password has been set."
        )
        return

    entered_password = check_password_entry.get()

    # IMPORTANT: Compare entered password with saved password
    if entered_password == password:
        messagebox.showinfo(
            "Success",
            "Password is correct! ✅"
        )
    else:
        messagebox.showerror(
            "Error",
            "Incorrect password!"
        )

    check_password_entry.delete(0, tk.END)


# ==========================================
# SHOW / HIDE PASSWORD
# ==========================================

def show_password():

    if show_password_var.get():
        new_password_entry.config(show="")
        confirm_password_entry.config(show="")
        old_password_entry.config(show="")
        change_new_password_entry.config(show="")
        change_confirm_password_entry.config(show="")
        check_password_entry.config(show="")
    else:
        new_password_entry.config(show="*")
        confirm_password_entry.config(show="*")
        old_password_entry.config(show="*")
        change_new_password_entry.config(show="*")
        change_confirm_password_entry.config(show="*")
        check_password_entry.config(show="*")


# ==========================================
# MAIN WINDOW
# ==========================================

root = tk.Tk()

root.title("Password Manager")

root.geometry("500x650")

root.resizable(False, False)


# ==========================================
# TITLE
# ==========================================

title_label = tk.Label(
    root,
    text="🔐 Password Manager",
    font=("Arial", 24, "bold")
)

title_label.pack(pady=20)


# ==========================================
# SHOW / HIDE CHECKBOX
# ==========================================

show_password_var = tk.BooleanVar()

show_password_check = tk.Checkbutton(
    root,
    text="Show Passwords",
    variable=show_password_var,
    command=show_password
)

show_password_check.pack(pady=5)


# ==========================================
# SET NEW PASSWORD SECTION
# ==========================================

set_frame = tk.LabelFrame(
    root,
    text="Set New Password",
    font=("Arial", 12, "bold"),
    padx=15,
    pady=15
)

set_frame.pack(
    fill="x",
    padx=20,
    pady=10
)


tk.Label(
    set_frame,
    text="New Password:"
).pack(anchor="w")


new_password_entry = tk.Entry(
    set_frame,
    width=40,
    show="*"
)

new_password_entry.pack(pady=5)


tk.Label(
    set_frame,
    text="Confirm Password:"
).pack(anchor="w")


confirm_password_entry = tk.Entry(
    set_frame,
    width=40,
    show="*"
)

confirm_password_entry.pack(pady=5)


tk.Button(
    set_frame,
    text="Set New Password",
    command=set_password,
    width=25
).pack(pady=10)


# ==========================================
# CHANGE PASSWORD SECTION
# ==========================================

change_frame = tk.LabelFrame(
    root,
    text="Change Password",
    font=("Arial", 12, "bold"),
    padx=15,
    pady=15
)

change_frame.pack(
    fill="x",
    padx=20,
    pady=10
)


tk.Label(
    change_frame,
    text="Old Password:"
).pack(anchor="w")


old_password_entry = tk.Entry(
    change_frame,
    width=40,
    show="*"
)

old_password_entry.pack(pady=5)


tk.Label(
    change_frame,
    text="New Password:"
).pack(anchor="w")


change_new_password_entry = tk.Entry(
    change_frame,
    width=40,
    show="*"
)

change_new_password_entry.pack(pady=5)


tk.Label(
    change_frame,
    text="Confirm New Password:"
).pack(anchor="w")


change_confirm_password_entry = tk.Entry(
    change_frame,
    width=40,
    show="*"
)

change_confirm_password_entry.pack(pady=5)


tk.Button(
    change_frame,
    text="Change Password",
    command=change_password,
    width=25
).pack(pady=10)


# ==========================================
# CHECK PASSWORD SECTION
# ==========================================

check_frame = tk.LabelFrame(
    root,
    text="Check Password",
    font=("Arial", 12, "bold"),
    padx=15,
    pady=15
)

check_frame.pack(
    fill="x",
    padx=20,
    pady=10
)


check_password_entry = tk.Entry(
    check_frame,
    width=40,
    show="*"
)

check_password_entry.pack(pady=5)


tk.Button(
    check_frame,
    text="Check Password",
    command=check_password,
    width=25
).pack(pady=5)


# ==========================================
# EXIT BUTTON
# ==========================================

tk.Button(
    root,
    text="Exit",
    command=root.destroy,
    width=20
).pack(pady=10)


# ==========================================
# START APPLICATION
# ==========================================

root.mainloop()

