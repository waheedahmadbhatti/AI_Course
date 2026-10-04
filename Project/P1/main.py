# import resources as r

# print(r.greet("Jahanzeb"))


# #call normal functions 
# r.greet("Ali")
# from resources import hccda
# std1=hccda('ALi',24,'m',16)
# std1.check_qualified()



# # CRETAE BANK ACC OBJECT 

# account=r.bank_account(title="Zebi",acc_num="39495959",balance=945969)


# #CALL DEPOSUIT

# account.deposit(2093044)


# # call withdrw 
# account.withdraw(2000)




# # print slip

# account.print_slip()

# # CREATE RECIVER ACCC
# reciver=r.bank_account(title="Bhatti ",acc_num="394sdd95959",balance=348485)

# # Tranfer Money 

# account.tranfer(1000,reciver)

from resources import bank_account as ba

ac1=ba(title="Asad",acc_num=10001,balance=2300)
ac2=ba(title="Ali",acc_num=10002)

ac1.tranfer(600,ac2)
ac2.print_slip()