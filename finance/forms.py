from django import forms
from finance.models import Transaction, BankAccount, CashAccount,\
    TransactionCategory,TaxCategory, CashTransfer
from django.forms.widgets import Select, TextInput, Textarea, CheckboxInput
from django.forms.fields import Field
from dal import autocomplete
setattr(Field, 'is_checkbox', lambda self: isinstance(self.widget, forms.CheckboxInput))
from django.utils.translation import ugettext_lazy as _


TRANSACTION_CATEGORY_TYPES = (
    ('','---------------'),
    ('income','Income'),
    ('expense','Expense'),
)


class BankAccountForm(forms.ModelForm):
    
    class Meta:
        model = BankAccount
        exclude = ['updator','creator','is_deleted','auto_id','a_id','balance','shop']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'ifsc': TextInput(attrs={'class': 'required form-control','placeholder' : 'IFSC'}),
            'branch': TextInput(attrs={'class': 'required form-control','placeholder' : 'Branch'}),
            'account_type': Select(attrs={'class': 'required form-control selectpicker'}),
            'account_no': TextInput(attrs={'class': 'required form-control','placeholder' : 'Account number'}),
            "first_time_balance" : TextInput(attrs={"class":"required form-control number","placeholder":"Enter amount"}),
            'cheque_return_charge' : TextInput(attrs={"class":"required form-control number","placeholder":"Cheque Return Charge"}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'ifsc' : {
                'required' : _("Ifsc field is required."),
            },
            'branch' : {
                'required' : _("Branch field is required."),
            },
            'account_type' : {
                'required' : _("Account Type field is required."),
            },
            'account_no' : {
                'required' : _("Account No field is required."),
            }
        }
        
        
class CashAccountForm(forms.ModelForm):
    
    class Meta:
        model = CashAccount
        exclude = ['updator','creator','is_system_generated','is_deleted','auto_id','a_id','balance','shop','user']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            "first_time_balance" : TextInput(attrs={"class":"required form-control number","placeholder":"Enter amount"}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'first_time_balance' : {
                'required' : _("First Time Balance field is required."),
            }
        }
        
        
class TransactionCategoryForm(forms.Form):
    
    class Meta:
        model = TransactionCategory
        name = forms.CharField(
        widget=forms.Textarea(attrs={'class':'required form-control',"rows":"5",'placeholder':'Enter category name(s)'}),
                help_text = "Seperate by commas. Duplicate entry will be skipped."
            )
        category_type = forms.ChoiceField(
        choices= TRANSACTION_CATEGORY_TYPES,
        widget=forms.Select(attrs={'class':'form-control required single selectpicker'})
            )
    

class TransactionCategoryModelForm(forms.ModelForm):
    
    class Meta:
        model = TransactionCategory
        exclude = ['updator','creator','is_system_generated','is_deleted','auto_id','shop','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'category_type' : Select(attrs={'class': 'required form-control selectpicker'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'category_type' : {
                'required' : _("Category Type field is required."),
            }
        }
        

class TaxCategoryForm(forms.ModelForm):
    
    class Meta:
        model = TaxCategory
        exclude = ['updator','creator','is_deleted','auto_id','shop','a_id']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control','placeholder' : 'Name'}),
            'tax': TextInput(attrs={'class': 'number required form-control','placeholder' : 'Tax'}),
        }
        error_messages = {
            'name' : {
                'required' : _("Name field is required."),
            },
            'tax' : {
                'required' : _("Tax field is required."),
            }
        }

        
class TransactionForm(forms.ModelForm): 
    
    class Meta:
        model = Transaction
        exclude = ['creator','updator','shop','staff','transaction_type','auto_id','shop','a_id','collect_amount','paid','date','first_transaction']
        widgets = {
            "transaction_category" : Select(attrs={"class":"single required form-control selectpicker"}),
            "transaction_mode" : Select(attrs={"class":"single required form-control selectpicker"}),
            "payment_mode" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "payment_to" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "bank_account" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "cash_account" : Select(attrs={"class":"single required form-control selectpicker"}),
            "amount" : TextInput(attrs={"class":"required form-control number","placeholder":"Enter amount"}),
            "cheque_details" : TextInput(attrs={"class":"bank_item cheque_item required form-control","rows":"5","placeholder":"Enter cheque details"}),
            "card_details" : Textarea(attrs={"class":"bank_item card_item required form-control","rows":"5","placeholder":"Enter card details"}),
            "is_cheque_withdrawed" : CheckboxInput(attrs={"class":"bank_item cheque_item form-control"}),
            "description" : TextInput(attrs={"class":"form-control","placeholder":"description"}),
            'cheque_date': TextInput(attrs={'class': 'bank_item cheque_item form-control date-picker','placeholder' : 'Date'}),
        }
        error_messages = {
            'transaction_category' : {
                'required' : _("Transaction Category field is required."),
            },
            'transaction_mode' : {
                'required' : _("Transaction Mode field is required."),
            },
            'payment_mode' : {
                'required' : _("Payment Mode field is required."),
            },
            'payment_to' : {
                'required' : _("Payment To field is required."),
            },
            'shop_credit_user' : {
                'required' : _("Shop Credit User field is required."),
            },
            'bank_account' : {
                'required' : _("Bank Account field is required."),
            },
            'cash_account' : {
                'required' : _("Cash Account field is required."),
            },
            'amount' : {
                'required' : _("Amount field is required."),
            },
            'cheque_details' : {
                'required' : _("Cheque Details field is required."),
            },
            'card_details' : {
                'required' : _("Card Details field is required."),
            },
            'date' : {
                'required' : _("Date field is required."),
            }
        }
        
    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields['transaction_category'].empty_label = None
        self.fields['bank_account'].empty_label = None
        self.fields['cash_account'].empty_label = None
        
        if self.fields['payment_to'].choices[0][0] == '':
            payment_to_choices = self.fields['payment_to'].choices
            del payment_to_choices[0]
            self.fields['payment_to'].choices = payment_to_choices
            
        if self.fields['payment_mode'].choices[0][0] == '':
            payment_mode_choices = self.fields['payment_mode'].choices
            del payment_mode_choices[0]
            self.fields['payment_mode'].choices = payment_mode_choices
        
        
    def clean(self):
        transaction_category = self.cleaned_data.get('transaction_category')
        shop_credit_user = self.cleaned_data.get('shop_credit_user')
        
        if transaction_category == "credit" or transaction_category == "debit":
            if not shop_credit_user:
                self._errors['shop_credit_user'] = self.error_class([
                    'Shop Credit User field is required. ']) 
            

class CreditDebitForm(forms.ModelForm): 
    
    class Meta:
        model = Transaction
        exclude = ['creator','updator','shop','staff','transaction_type','auto_id','shop','a_id','collect_amount','paid','first_transaction']
        widgets = {
            "transaction_category" : Select(attrs={"class":"single required form-control selectpicker"}),
            "transaction_mode" : Select(attrs={"class":"single required form-control selectpicker"}),
            "payment_mode" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "payment_to" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "bank_account" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "cash_account" : Select(attrs={"class":"single required form-control selectpicker"}),
            "amount" : TextInput(attrs={"class":"required form-control number","placeholder":"Enter amount"}),
            "cheque_details" : TextInput(attrs={"class":"bank_item cheque_item required form-control","rows":"5","placeholder":"Enter cheque details"}),
            "card_details" : Textarea(attrs={"class":"bank_item card_item required form-control","rows":"5","placeholder":"Enter card details"}),
            "is_cheque_withdrawed" : CheckboxInput(attrs={"class":"bank_item cheque_item form-control"}),
            "date" : TextInput(attrs={"class":"date-time-picker required form-control","placeholder":"Enter date"}),
            "description" : TextInput(attrs={"class":"form-control","placeholder":"description"}),
            'cheque_date': TextInput(attrs={'class': 'bank_item cheque_item form-control date-picker','placeholder' : 'Date'}),
        }
        error_messages = {
            'transaction_category' : {
                'required' : _("Transaction Category field is required."),
            },
            'transaction_mode' : {
                'required' : _("Transaction Mode field is required."),
            },
            'payment_mode' : {
                'required' : _("Payment Mode field is required."),
            },
            'payment_to' : {
                'required' : _("Payment To field is required."),
            },
            'shop_credit_user' : {
                'required' : _("Shop Credit User field is required."),
            },
            'bank_account' : {
                'required' : _("Bank Account field is required."),
            },
            'cash_account' : {
                'required' : _("Cash Account field is required."),
            },
            'amount' : {
                'required' : _("Amount field is required."),
            },
            'cheque_details' : {
                'required' : _("Cheque Details field is required."),
            },
            'card_details' : {
                'required' : _("Card Details field is required."),
            },
            'date' : {
                'required' : _("Date field is required."),
            }
        }
        
    def __init__(self, *args, **kwargs):
        super(CreditDebitForm, self).__init__(*args, **kwargs)
        self.fields['transaction_category'].empty_label = None
        self.fields['bank_account'].empty_label = None
        self.fields['cash_account'].empty_label = None
        
        if self.fields['payment_to'].choices[0][0] == '':
            payment_to_choices = self.fields['payment_to'].choices
            del payment_to_choices[0]
            self.fields['payment_to'].choices = payment_to_choices
            
        if self.fields['payment_mode'].choices[0][0] == '':
            payment_mode_choices = self.fields['payment_mode'].choices
            del payment_mode_choices[0]
            self.fields['payment_mode'].choices = payment_mode_choices
        
        
    def clean(self):
        transaction_category = self.cleaned_data.get('transaction_category')
        shop_credit_user = self.cleaned_data.get('shop_credit_user')
        
        if transaction_category == "credit" or transaction_category == "debit":
            if not shop_credit_user:
                self._errors['shop_credit_user'] = self.error_class([
                    'Shop Credit User field is required. ']) 


class SalaryPaymentForm(forms.ModelForm):
   
    class Meta:
        model = Transaction
        exclude = ['creator','updator','transaction_category','auto_id','transaction_type','sale','title','is_deleted','shop','a_id','vendor','sale_return','purchase_return','description','collect_amount','paid','customer','asset_purchase','purchase','vender_payment','customer_payment','staff_salary','first_transaction']
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staffs:staffs_autocomplete', attrs={'data-placeholder': 'Staff', 'data-minimum-input-length': 1},),
            "transaction_mode" : Select(attrs={"class":"single required form-control selectpicker"}),
            "payment_mode" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "payment_to" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "bank_account" : Select(attrs={"class":"single bank_item required form-control selectpicker"}),
            "cash_account" : Select(attrs={"class":"single required form-control selectpicker"}),
            "amount" : TextInput(attrs={"class":"required number form-control","placeholder":"Enter amount"}),
            "cheque_details" : Textarea(attrs={"class":"bank_item cheque_item text required form-control","rows":"5","placeholder":"Enter cheque details"}),
            "card_details" : Textarea(attrs={"class":"bank_item card_item required text form-control","rows":"5","placeholder":"Enter card details"}),
            "is_cheque_withdrawed" : CheckboxInput(attrs={"class":"bank_item cheque_item form-control"}),
            "date" : TextInput(attrs={"class":"date-time-picker required form-control","placeholder":"Enter Time"}),
            'cheque_date': TextInput(attrs={'class': 'bank_item cheque_item form-control date-picker','placeholder' : 'Date'}),
        }
        labels = {
        "date" : "Time"
        }
        error_messages = {
            
            'transaction_mode' : {
                'required' : _("Transaction Mode field is required."),
            },
            'payment_mode' : {
                'required' : _("Payment Mode field is required."),
            },
            'payment_to' : {
                'required' : _("Payment To field is required."),
            },
            'bank_account' : {
                'required' : _("Bank Account field is required."),
            },
            'cash_account' : {
                'required' : _("Cash Account field is required."),
            },
            'amount' : {
                'required' : _("Amount field is required."),
            },
            'cheque_details' : {
                'required' : _("Cheque Details field is required."),
            },
            'card_details' : {
                'required' : _("Card Details field is required."),
            },
            'date' : {
                'required' : _("Date field is required."),
            },
        }
    
    def __init__(self, *args, **kwargs):
        super(SalaryPaymentForm, self).__init__(*args, **kwargs)
        self.fields['bank_account'].empty_label = None
        self.fields['cash_account'].empty_label = None
        
        if self.fields['payment_to'].choices[0][0] == '':
            payment_to_choices = self.fields['payment_to'].choices
            del payment_to_choices[0]
            self.fields['payment_to'].choices = payment_to_choices
            
        if self.fields['payment_mode'].choices[0][0] == '':
            payment_mode_choices = self.fields['payment_mode'].choices
            del payment_mode_choices[0]
            self.fields['payment_mode'].choices = payment_mode_choices


class CashTransferForm(forms.ModelForm): 

    def __init__(self, *args, **kwargs):
        super(CashTransferForm, self).__init__(*args, **kwargs)
        self.fields['to_cash_account'].empty_label = None
    
    class Meta:
        model = CashTransfer
        exclude = ['creator','updator','auto_id','a_id','shop']
        widgets = {
            "from_cash_account" : Select(attrs={"class":"selectpicker bank_item required form-control "}),
            "to_cash_account" : Select(attrs={"class":"selectpicker bank_item required form-control "}),
            'distributor': autocomplete.ModelSelect2(url='distributors:distributor_autocomplete', attrs={'data-placeholder': 'Distributor', 'data-minimum-input-length': 1},),
            "amount" : TextInput(attrs={"class":"required form-control number","placeholder":"Enter amount"}),
        }
        
        error_messages = {
            'from_cash_account' : {
                'required' : _("From Cash Account field is required."),
            },
            'to_cash_account' : {
                'required' : _("To Cash Account field is required."),
            },
            'distributor' : {
                'required' : _("Distributor field is required."),
            },
            'amount' : {
                'required' : _("Amount field is required."),
            }
        }


class LedgerForm(forms.Form):
    from_date = forms.DateField(widget=forms.TextInput(attrs={"class": 'form-control date-picker'}))
    to_date = forms.DateField(widget=forms.TextInput(attrs={"class": 'form-control date-picker'}))
