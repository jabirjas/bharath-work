from vendors.models import Vendor


def update_vendor_credit_debit(pk,transaction_type,amount):
    if amount > 0:
        vendor = Vendor.objects.get(pk=pk)
        credit = vendor.credit
        debit = vendor.debit
        
        vendor_objects = Vendor.objects.filter(pk=pk)
        
        if transaction_type == "credit":
            if debit > 0:
                debit_balance = debit - amount                
                if debit_balance < 0:
                    abs_debit_balance = abs(debit_balance)
                    vendor_objects.update(debit=0)
                    vendor_objects.update(credit=abs_debit_balance)
                else:
                    vendor_objects.update(debit=debit_balance)
            else:
                vendor_objects.update(credit=credit+amount)
            
        elif transaction_type == "debit":
            if credit > 0:
                credit_balance = credit - amount                
                if credit_balance < 0:
                    abs_credit_balance = abs(credit_balance)
                    vendor_objects.update(credit=0,debit=abs_credit_balance)
                else:
                    vendor_objects.update(credit=credit_balance)
            else:
                vendor_objects.update(debit=debit+amount)
    
    
def get_vendor_credit(pk):
    vendor = Vendor.objects.get(pk=pk)
    credit = vendor.credit
    return credit


def get_vendor_debit(pk):
    vendor = Vendor.objects.get(pk=pk)
    debit = vendor.debit
    return debit
    
    