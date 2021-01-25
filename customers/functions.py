from customers.models import Customer


def update_customer_credit_debit(pk,transaction_type,amount):
    if amount > 0:
        customer = Customer.objects.get(pk=pk)
        credit = customer.credit
        debit = customer.debit
        
        customer_objects = Customer.objects.filter(pk=pk)
        
        if transaction_type == "credit":
            if debit > 0:
                debit_balance = debit - amount                
                if debit_balance < 0:
                    abs_debit_balance = abs(debit_balance)
                    customer_objects.update(debit=0)
                    customer_objects.update(credit=abs_debit_balance)
                else:
                    customer_objects.update(debit=debit_balance)
            else:
                customer_objects.update(credit=credit+amount)
            
        elif transaction_type == "debit":
            if credit > 0:
                credit_balance = credit - amount    
                #printcredit_balance            
                if credit_balance < 0:
                    abs_credit_balance = abs(credit_balance)
                    customer_objects.update(credit=0,debit=abs_credit_balance)
                else:
                    customer_objects.update(credit=credit_balance)
            else:
                customer_objects.update(debit=debit+amount)
    
    
def get_customer_credit(pk):
    customer = Customer.objects.get(pk=pk)
    credit = customer.credit
    return credit


def get_customer_debit(pk):
    customer = Customer.objects.get(pk=pk)
    debit = customer.debit
    return debit
    

def update_customer_return_amount(pk,transaction_type,amount):
    if amount > 0:
        customer = Customer.objects.get(pk=pk)
        return_amount = customer.return_amount
        
        customer_objects = Customer.objects.filter(pk=pk)
        
        if transaction_type == "increase":
            total_return_amount = return_amount + amount   
            customer_objects.update(return_amount=total_return_amount)
        elif transaction_type == "decrease":
            total_return_amount = return_amount - amount   
            customer_objects.update(return_amount=total_return_amount)
    