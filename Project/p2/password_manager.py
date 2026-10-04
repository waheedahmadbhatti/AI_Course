
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


# Function to set a new password
def set_password():
    new_password = input("Enter new password: ")

    # IMPORTANT: Check password length
    if len(new_password) < 8:
        print("❌ Password must be at least 8 characters long.")
        return

    # IMPORTANT: Check for uppercase letter
    if not any(char.isupper() for char in new_password):
        print("❌ Password must contain at least one uppercase letter.")
        return

    # IMPORTANT: Check for special character
    if not any(not char.isalnum() for char in new_password):
        print("❌ Password must contain at least one special character.")
        return

    # Confirm the new password
    confirm_password = input("Confirm new password: ")

    # IMPORTANT: Check whether both passwords match
    if new_password != confirm_password:
        print("❌ Passwords do not match!")
        return

    # Save the new password
    with open("password.txt", "w") as f:
        f.write(new_password)

    print("✅ Password set successfully!")


# Function to change existing password
def change_password():
    password = get_password()

    # If no password exists
    if not password:
        print("❌ No password has been set yet.")
        return

    # STEP 1: Verify old password
    old_password = input("Enter your old password: ")

    # IMPORTANT: Verify the old password
    if old_password != password:
        print("❌ Incorrect old password!")
        return

    # STEP 2: Enter new password
    new_password = input("Enter new password: ")

    # IMPORTANT: Password must be at least 8 characters
    if len(new_password) < 8:
        print("❌ Password must be at least 8 characters long.")
        return

    # IMPORTANT: Password must contain uppercase letter
    if not any(char.isupper() for char in new_password):
        print("❌ Password must contain at least one uppercase letter.")
        return

    # IMPORTANT: Password must contain special character
    if not any(not char.isalnum() for char in new_password):
        print("❌ Password must contain at least one special character.")
        return

    # STEP 3: Confirm password
    confirm_password = input("Confirm new password: ")

    # IMPORTANT: Check confirmation
    if new_password != confirm_password:
        print("❌ Passwords do not match!")
        return

    # STEP 4: Save new password
    with open("password.txt", "w") as f:
        f.write(new_password)

    print("✅ Password changed successfully!")


# Function to check whether a password exists
def check_password():
    password = get_password()

    if not password:
        print("❌ No password has been set.")
        return

    entered_password = input("Enter your password: ")

    # IMPORTANT: Compare entered password with saved password
    if entered_password == password:
        print("✅ Password is correct!")
    else:
        print("❌ Incorrect password!")


# ==========================================
# MAIN MENU
# ==========================================

while True:

    print("\n================================")
    print("       PASSWORD MANAGER")
    print("================================")

    print("1. Set New Password")
    print("2. Change Password")
    print("3. Check Password")
    print("4. Exit")

    choice = input("Enter your choice: ")

    # User selects option 1
    if choice == "1":
        set_password()

    # User selects option 2
    elif choice == "2":
        change_password()

    # User selects option 3
    elif choice == "3":
        check_password()

    # User selects option 4
    elif choice == "4":
        print("Goodbye! 👋")
        break

    # Invalid option
    else:
        print("❌ Invalid choice! Please select 1, 2, 3, or 4.")

