from django.conf.urls import url
from . import views
from finance.autocomplete_light_registry import StaffAutocomplete, TaxCategoryAutocomplete


urlpatterns = [
    url(r'^tax-category-autocomplete/$',TaxCategoryAutocomplete.as_view(create_field='tax'),name='tax_category_autocomplete'),

    url(r'^$', views.dashboard,name='dashboard'), 

    url(r'^bank-account/create/$',views.create_bank_account,name='create_bank_account'),
    url(r'^bank-account/edit(?P<pk>.*)/$',views.edit_bank_account,name='edit_bank_account'),
    url(r'^bank-accounts/$',views.bank_accounts,name='bank_accounts'),
    url(r'^bank-account/view/(?P<pk>.*)/$',views.bank_account,name='bank_account'),
    url(r'^bank-account/delete/(?P<pk>.*)/$',views.delete_bank_account,name='delete_bank_account'),
    url(r'^bank-account/delete-selected/$', views.delete_selected_bank_accounts, name='delete_selected_bank_accounts'),

    url(r'^cash-account/create/$',views.create_cash_account,name='create_cash_account'),
    url(r'^cash-account/edit/(?P<pk>.*)$',views.edit_cash_account,name='edit_cash_account'),
    url(r'^cash-accounts/$',views.cash_accounts,name='cash_accounts'),
    url(r'^cash-account/view/(?P<pk>.*)/$',views.cash_account,name='cash_account'),
    url(r'^cash-account/delete/(?P<pk>.*)$',views.delete_cash_account,name='delete_cash_account'),
    url(r'^cash-account/delete-selected/$', views.delete_selected_cash_accounts, name='delete_selected_cash_accounts'),

    url(r'^transaction-category/create/$',views.create_transaction_category,name='create_transaction_category'),
    url(r'^transaction-category/edit/(?P<pk>.*)/$',views.edit_transaction_category,name='edit_transaction_category'),
    url(r'^transaction-categories/',views.transaction_categories,name='transaction_categories'),
    url(r'^transaction-category/view/(?P<pk>.*)/$',views.transaction_category,name='transaction_category'),
    url(r'^transaction-category/delete/(?P<pk>.*)/$',views.delete_transaction_category,name='delete_transaction_category'),
    url(r'^transaction-category/delete-selected/$', views.delete_selected_transaction_categories, name='delete_selected_transaction_categories'),

    url(r'^income/create/$',views.create_income,name='create_income'),
    url(r'^income/edit/(?P<pk>.*)/$',views.edit_income,name='edit_income'),
    
    url(r'^transactions/$',views.transactions,name='transactions'),
    url(r'^transaction/view/(?P<pk>.*)/$',views.transaction,name='transaction'),
    url(r'^transaction/delete/(?P<pk>.*)/$',views.delete_transaction,name='delete_transaction'),
    url(r'^transaction/delete-selected/$', views.delete_selected_transactions, name='delete_selected_transactions'),

    url(r'^expense/create/$',views.create_expense,name='create_expense'),
    url(r'^expense/edit(?P<pk>.*)/$',views.edit_expense,name='edit_expense'),
    
    url(r'^staff-autocomplete/$',StaffAutocomplete.as_view(),name='staff_autocomplete'),

    url(r'^tax-category/create/$', views.create_tax_category, name='create_tax_category'),
    url(r'^tax-categories/$', views.tax_categories, name='tax_categories'),
    url(r'^tax-category/edit/(?P<pk>.*)/$', views.edit_tax_category, name='edit_tax_category'),
    url(r'^tax-category/(?P<pk>.*)/$', views.tax_category, name='tax_category'),
    url(r'^delete-tax-category/(?P<pk>.*)/$', views.delete_tax_category, name='delete_tax_category'),
    url(r'^tax-category/delete-selected/$', views.delete_selected_tax_categories, name='delete_selected_tax_categories'),

    url(r'^create-salary-payment/$',views.create_salary_payment,name='create_salary_payment'),
    url(r'^create-salary-payment-popup/$',views.create_salary_payment_ajax,name='create_salary_payment_ajax'),
    url(r'^salary-payment/edit/(?P<pk>.*)/$',views.edit_salary_payment,name='edit_salary_payment'),
    url(r'^salary-payments/$',views.salary_payments,name='salary_payments'),

    url(r'^cash-transfer/create/$',views.create_cash_transfer,name='create_cash_transfer'),
    url(r'^cash-transfers/$',views.cash_transfers,name='cash_transfers'),
    url(r'^cash-transfer/(?P<pk>.*)/$',views.cash_transfer,name='cash_transfer'),
    url(r'^delete-cash-transfer/(?P<pk>.*)/$',views.delete_cash_transfer,name='delete_cash_transfer'),
    url(r'^delete-selected-cash-transfers/$', views.delete_selected_cash_transfers, name='delete_selected_cash_transfers'),

    url(r'^get-cash-account-list/$',views.get_cash_account_list,name='get_cash_account_list'),
    url(r'^get-cash-balance/$',views.get_cash_balance,name='get_cash_balance'),

    url(r'^balance-sheet/create/$',views.create_balance_sheet,name='create_balance_sheet'),
    url(r'^balance-sheet/$',views.balance_sheet,name='balance_sheet'),


    url(r'^get-tax/$',views.get_tax,name='get_tax'),

]