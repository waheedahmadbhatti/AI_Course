

# for making file and saving in file 

# password=input('enter new password')
# with open('password.txt','w') as f:
#     f.write(password)

#     print('Password saved in file')



# now open file alreay created and read that 


# with open('password.txt', 'r') as f:
#     password=f.read()
#     print(password)

# # change password

# new =input('enter new password')
# with open('password.txt','w') as f:
#     f.write(new)



# full functional program to reset password with validations


# Read the existing password from the file
with open('password.txt', 'r') as f:
    password = f.read().strip()


# ==============================
# STEP 1: VERIFY OLD PASSWORD
# ==============================

old_password = input("Enter your old password: ")

# Check whether the entered old password matches the saved password
if old_password != password:
    print("Incorrect old password!")
else:

    # ==============================
    # STEP 2: ENTER NEW PASSWORD
    # ==============================

    new_password = input("Enter new password: ")

    # ==============================
    # PASSWORD VALIDATION
    # ==============================

    # Check password length
    if len(new_password) < 8:
        print("Password must be at least 8 characters long.")

    # Check for at least one uppercase letter
    elif not any(char.isupper() for char in new_password):
        print("Password must contain at least one uppercase letter.")

    # Check for at least one special character
    elif not any(not char.isalnum() for char in new_password):
        print("Password must contain at least one special character.")

    else:

        # ==============================
        # STEP 3: CONFIRM NEW PASSWORD
        # ==============================

        confirm_password = input("Confirm new password: ")

        # Check whether both new passwords are the same
        if new_password != confirm_password:
            print("Passwords do not match!")

        else:

            # ==============================
            # STEP 4: SAVE NEW PASSWORD
            # ==============================

            with open('password.txt', 'w') as f:
                f.write(new_password)

            print("Password changed successfully!")