from users.functions import shop_access, get_current_shop
from main.functions import get_account_balance,get_current_role
from users.models import Notification
from main.models import Mode, Shop, ShopAccess
from staffs.models import Staff
import datetime
from finance.forms import SalaryPaymentForm
from distributors.models import Distributor


def main_context(request):
    current_shop = get_current_shop(request)
    today = datetime.date.today()
    salary_payment_form = SalaryPaymentForm(initial={"date":today})
    is_superuser = False
    logged_username = ""
    if "set_user_timezone" in request.session:
        user_session_ok = True
        user_time_zone = request.session['set_user_timezone']
    else:
        user_session_ok = False
        user_time_zone = "Asia/Kolkata"

    current_theme = 'cyan-600'
    block_auto_redirect = False
    remove_previous_balance_from_bill = False
    default_paid_value = False
    salesman = False
    user_instance =[]
    can_sale_purchase_request = False
    current_theme_loader = "Teal"
    if current_shop:
        current_theme = current_shop.theme
        current_theme_loader = "Teal"
        if current_theme == 'teal':
            current_theme_loader = "Teal"
        elif current_theme == 'blue':
            current_theme_loader = "Blue"
        elif current_theme == 'bluegrey':
            current_theme_loader = "Blue-Grey"
        elif current_theme == 'cyan-600':
            current_theme_loader = "Cyan"
        elif current_theme == 'green':
            current_theme_loader = "Green"
        elif current_theme == 'lightgreen':
            current_theme_loader = "Light-Green"
        elif current_theme == 'purple':
            current_theme_loader = "Purple"
        elif current_theme == 'pink':
            current_theme_loader = "Pink"
        elif current_theme == 'brown':
            current_theme_loader = "Brown"
        elif current_theme == 'grey':
            current_theme_loader = "Grey"
        elif current_theme == 'orange':
            current_theme_loader = "Orange"
        block_auto_redirect = current_shop.block_auto_redirect
        remove_previous_balance_from_bill = current_shop.remove_previous_balance_from_bill
        default_paid_value = current_shop.default_paid_value
    current_role = "user"
    if request.user.is_authenticated:
        if request.user.is_superuser:
            logged_username = "SuperAdmin"
        else:
            logged_username = request.user.username

        if ShopAccess.objects.filter(user=request.user).exists():
            if request.user.is_superuser:
                is_superuser=True
        current_role = get_current_role(request)
        if current_role == "staff":
            user_instance = Staff.objects.get(user=request.user,shop=current_shop)
        if current_role == 'distributor':
            distributor = Distributor.objects.get(user=request.user)
            if distributor.is_salesman:
                salesman = True
            else:
                can_sale_purchase_request = True
        recent_notifications = Notification.objects.filter(user=request.user,is_deleted=False)
    else:
        recent_notifications = []

    active_parent = request.GET.get('active_parent')
    active = request.GET.get('active')
    return {
        'app_title' : "Bharath Expo",
        "user_session_ok" : user_session_ok,
        "user_time_zone" : user_time_zone,
        "confirm_delete_message" : "Are you sure want to delete this item. All associated data may be removed.",
        "revoke_access_message" : "Are you sure to revoke this user's login access",
        "confirm_shop_delete_message" : "Your shop will deleted permanantly. All data will lost.",
        "confirm_delete_selected_message" : "Are you sure to delete all selected items.",
        "confirm_read_message" : "Are you sure want to mark as read this item.",
        "confirm_read_selected_message" : "Are you sure to mark as read all selected items.",
        "confirm_cheque_withdraw" : "Are you sure to withdraw.",
        "confirm_cheque_return" : "Are you sure to Return.",
        'domain' : request.META['HTTP_HOST'],
        "shop_access" : shop_access(request),
        'current_shop' : current_shop,
        "current_role" : current_role,
        "account_balance" : get_account_balance(request,request.user),
        "current_theme" : current_theme,
        "user_instance" : user_instance,
        "is_superuser" : is_superuser,
        "active_parent" : active_parent,
        "active_menu" : active,
        "recent_notifications" : recent_notifications,
        "block_auto_redirect" : block_auto_redirect,
        "current_theme_loader" : current_theme_loader,
        "default_paid_value" : default_paid_value ,

        "salary_payment_form":salary_payment_form,
        "remove_previous_balance_from_bill" : remove_previous_balance_from_bill,
        "salesman" : salesman,
        "can_sale_purchase_request" : can_sale_purchase_request,
        "logged_username" : logged_username
    }
