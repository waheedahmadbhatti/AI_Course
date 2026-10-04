import tkinter as tk
from tkinter import messagebox


def get_password():
    try:
        with open("password.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def is_valid(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(not c.isalnum() for c in password):
        return "Password must contain at least one special character."
    return ""


def set_password():
    new = new_password_entry.get()
    confirm = confirm_password_entry.get()

    if not new or not confirm:
        messagebox.showerror("Error", "Please enter and confirm your password.")
        return

    error = is_valid(new)
    if error:
        messagebox.showerror("Invalid Password", error)
        return

    if new != confirm:
        messagebox.showerror("Error", "Passwords do not match!")
        return

    with open("password.txt", "w") as f:
        f.write(new)

    messagebox.showinfo("Success", "Password set successfully!")

    new_password_entry.delete(0, tk.END)
    confirm_password_entry.delete(0, tk.END)


def change_password():
    saved = get_password()

    if not saved:
        messagebox.showerror("Error", "No password has been set yet.")
        return

    old = old_password_entry.get()
    new = change_new_password_entry.get()
    confirm = change_confirm_password_entry.get()

    if not old or not new or not confirm:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    if old != saved:
        messagebox.showerror("Error", "Incorrect old password!")
        return

    error = is_valid(new)
    if error:
        messagebox.showerror("Invalid Password", error)
        return

    if new != confirm:
        messagebox.showerror("Error", "Passwords do not match!")
        return

    with open("password.txt", "w") as f:
        f.write(new)

    messagebox.showinfo("Success", "Password changed successfully!")

    old_password_entry.delete(0, tk.END)
    change_new_password_entry.delete(0, tk.END)
    change_confirm_password_entry.delete(0, tk.END)


def check_password():
    saved = get_password()

    if not saved:
        messagebox.showerror("Error", "No password has been set.")
        return

    entered = check_password_entry.get()

    if entered == saved:
        messagebox.showinfo("Success", "Password is correct!")
    else:
        messagebox.showerror("Error", "Incorrect password!")

    check_password_entry.delete(0, tk.END)


def toggle_password():
    show = "" if show_password_var.get() else "*"
    for entry in (new_password_entry, confirm_password_entry,
                  old_password_entry, change_new_password_entry,
                  change_confirm_password_entry, check_password_entry):
        entry.config(show=show)


def make_entry(parent):
    return tk.Entry(parent, width=40, show="*")


root = tk.Tk()
root.title("Password Manager")
root.geometry("500x650")
root.resizable(False, False)

tk.Label(root, text="Password Manager",
         font=("Arial", 24, "bold")).pack(pady=20)

show_password_var = tk.BooleanVar()
tk.Checkbutton(root, text="Show Passwords", variable=show_password_var,
               command=toggle_password).pack(pady=5)

# Set new password
set_frame = tk.LabelFrame(root, text="Set New Password",
                          font=("Arial", 12, "bold"), padx=15, pady=15)
set_frame.pack(fill="x", padx=20, pady=10)

tk.Label(set_frame, text="New Password:").pack(anchor="w")
new_password_entry = make_entry(set_frame)
new_password_entry.pack(pady=5)

tk.Label(set_frame, text="Confirm Password:").pack(anchor="w")
confirm_password_entry = make_entry(set_frame)
confirm_password_entry.pack(pady=5)

tk.Button(set_frame, text="Set New Password", command=set_password,
          width=25).pack(pady=10)

# Change password
change_frame = tk.LabelFrame(root, text="Change Password",
                             font=("Arial", 12, "bold"), padx=15, pady=15)
change_frame.pack(fill="x", padx=20, pady=10)

tk.Label(change_frame, text="Old Password:").pack(anchor="w")
old_password_entry = make_entry(change_frame)
old_password_entry.pack(pady=5)

tk.Label(change_frame, text="New Password:").pack(anchor="w")
change_new_password_entry = make_entry(change_frame)
change_new_password_entry.pack(pady=5)

tk.Label(change_frame, text="Confirm New Password:").pack(anchor="w")
change_confirm_password_entry = make_entry(change_frame)
change_confirm_password_entry.pack(pady=5)

tk.Button(change_frame, text="Change Password", command=change_password,
          width=25).pack(pady=10)

# Check password
check_frame = tk.LabelFrame(root, text="Check Password",
                            font=("Arial", 12, "bold"), padx=15, pady=15)
check_frame.pack(fill="x", padx=20, pady=10)

check_password_entry = make_entry(check_frame)
check_password_entry.pack(pady=5)

tk.Button(check_frame, text="Check Password", command=check_password,
          width=25).pack(pady=5)

tk.Button(root, text="Exit", command=root.destroy, width=20).pack(pady=10)

root.mainloop()
