institute_name="Cs Technologies"
course_name="AI"



def greet(name):
    print('Welcome', name)
    print('You are at', institute_name,'in',course_name,'class')



class hccda:
    def __init__(self,name,age,gender,max_edu):
        self.name=name
        self.age=age
        self.gender=gender
        self.max_edu=max_edu

    def  check_qualified(self):
        if(self.age>18 and self.age<40):
            if(self.max_edu>=16):
           
             print("You are eligible for this course")
            else:
                print('Sorry you need 16 years education to enrolment in this programe')
        else:
            print('Sorry your age is not godd fit for this programe')



# OOP MASTER  CLASS 

class bank_account:
    bank_name="CS Banking System"
    t_fee=20
    def __init__(self,title,acc_num,balance=0):
        self.title=title
        self.acc_num=acc_num
        self.__balance=balance

    def deposit(self,amount):
        if(amount>0):
            self.__balance+=amount
            print("Deposit Successfully")
        else:
            print("Please Enter Legal Amount")

    def withdraw(self,amount):
        if(self.__balance+self.t_fee>amount):
            self.__balance-=amount
            self.__transaction_fee()
            print("Withdraw SUccessfully")
        else:
            print("Please Enter valid amount ",print_slip())
    
    def __transaction_fee(self):
        self.__balance-=self.t_fee

    def print_slip(self):
        print("-"*40)
        print(f"Hello {self.title} This is {self.bank_name}")
        print("-"*40)
        print('Your Account Number is ', self.acc_num)
        print('Your Balance is ', self.__balance)
        print("-"*40)

    def tranfer(self,amount,receiver):
        if(self.__balance + self.t_fee>amount):
           self.__balance-=amount
           self.__transaction_fee()
           receiver.__balance+=amount
           print("Transactions Successfull")
        else:
            print("Invalid AMount")
            self.print_slip()

    @classmethod

    def update_t_fetch(cls,amount):
        cls.t_fee=amount
        print("Updated to",amount)

    @classmethod

    def greet():
        print("Hello this is static method")

    # def __del__(self):
    #     print("Your account have been deleted succesffully ")

    def __str__(self):
       return f"YOur account balance is {self.__balanc}"        