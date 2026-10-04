# Password manager with menu


def get_password():
    try:
        with open("password.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def is_valid(password):
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return False
    if not any(c.isupper() for c in password):
        print("Password must contain at least one uppercase letter.")
        return False
    if not any(not c.isalnum() for c in password):
        print("Password must contain at least one special character.")
        return False
    return True


def set_password():
    new = input("Enter new password: ")

    if not is_valid(new):
        return

    confirm = input("Confirm new password: ")

    if new != confirm:
        print("Passwords do not match!")
        return

    with open("password.txt", "w") as f:
        f.write(new)

    print("Password set successfully!")


def change_password():
    saved = get_password()

    if not saved:
        print("No password has been set yet.")
        return

    old = input("Enter your old password: ")

    if old != saved:
        print("Incorrect old password!")
        return

    new = input("Enter new password: ")

    if not is_valid(new):
        return

    confirm = input("Confirm new password: ")

    if new != confirm:
        print("Passwords do not match!")
        return

    with open("password.txt", "w") as f:
        f.write(new)

    print("Password changed successfully!")


def check_password():
    saved = get_password()

    if not saved:
        print("No password has been set.")
        return

    entered = input("Enter your password: ")

    if entered == saved:
        print("Password is correct!")
    else:
        print("Incorrect password!")


while True:
    print("\n--- PASSWORD MANAGER ---")
    print("1. Set New Password")
    print("2. Change Password")
    print("3. Check Password")
    print("4. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        set_password()
    elif choice == "2":
        change_password()
    elif choice == "3":
        check_password()
    elif choice == "4":
        print("Goodbye!")
        break
    else:
        print("Invalid choice! Please select 1, 2, 3, or 4.")
