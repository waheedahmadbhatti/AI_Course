# Password reset program


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


with open("password.txt", "r") as f:
    saved = f.read().strip()

old = input("Enter your old password: ")

if old != saved:
    print("Incorrect old password!")
else:
    new = input("Enter new password: ")

    if is_valid(new):
        again = input("Confirm new password: ")

        if new != again:
            print("Passwords do not match!")
        else:
            with open("password.txt", "w") as f:
                f.write(new)

            print("Password changed successfully!")
