import os
import string
import random
import xhtml2pdf.pisa as pisa
from cgi import escape
from django.template.loader import get_template
from django.template import Context
from io import StringIO
from django.http import HttpResponse
from django.conf import settings
from users.models import AccountBalance
from decimal import Decimal
from users.functions import get_current_shop
from main.models import Shop, ShopAccess


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_unique_id(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_form_errors(args,formset=False):
    message = ''
    if not formset:
        for field in args:
            if field.errors:
                message += field.errors  + "|"
        for err in args.non_field_errors():
            message += str(err) + "|"

    elif formset:
        for form in args:
            for field in form:
                if field.errors:
                    message +=field.errors + "|"
            for err in form.non_field_errors():
                message += str(err) + "|"
    return message[:-1]


def fetch_resources(uri, rel):
    import os.path
    path = os.path.join(settings.STATIC_FILE_ROOT,uri.replace(settings.STATIC_URL, ""))
    return path


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), result,link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def get_auto_id(model):
    auto_id = 1
    latest_auto_id =  model.objects.all().order_by("-date_added")[:1]
    if latest_auto_id:
        for auto in latest_auto_id:
            auto_id = auto.auto_id + 1
    return auto_id



def get_a_id(model,request):
    a_id = 1
    current_shop = get_current_shop(request)
    latest_a_id =  model.objects.filter(shop=current_shop).order_by("-date_added")[:1]
    if latest_a_id:
        for auto in latest_a_id:
            a_id = auto.a_id + 1
    return a_id


def get_timezone(request):
    if "set_user_timezone" in request.session:
        user_time_zone = request.session['set_user_timezone']
    else:
        user_time_zone = "Asia/Kolkata"
    return user_time_zone


def get_account_balance(request,user):
    balance = 0
    if request.user.is_authenticated:
        if AccountBalance.objects.filter(user=user).exists():
            balance = user.accountbalance.balance

    return balance


def get_free_amount(request):
    return Decimal(270)


def daily_rate():
    return Decimal(9)


def get_low_balance_limit():
    return Decimal(90)


def get_currency(user=None):
    return "Rs"


def minimum_amount():
    return Decimal(250)


def invite_code_amount():
    return Decimal(270)


def promo_code_amount():
    return Decimal(135)


def get_roles(request):
    roles = []
    if request.user.is_authenticated:
        current_shop = get_current_shop(request)
        shop_access = ShopAccess.objects.filter(shop=current_shop,user=request.user,is_accepted=True)
        for access in shop_access:
            roles.append(access.group.name)

    return roles


def get_current_role(request):
    is_shop_superadmin = False
    is_shop_administrator = False
    is_shop_staff = False
    is_shop_customer = False
    is_shop_vendor = False
    is_shop_distributor = False

    current_shop = get_current_shop(request)

    if request.user.is_authenticated and current_shop:

        if Shop.objects.filter(pk=current_shop.pk,creator=request.user).exists():
            is_shop_superadmin = True
        if request.user.is_superuser:
            is_shop_superadmin = True

        if ShopAccess.objects.filter(user=request.user,shop=current_shop,group__name="administrator").exists():
            is_shop_administrator = True

        if ShopAccess.objects.filter(user=request.user,shop=current_shop,group__name="staff").exists():
            is_shop_staff = True

        if ShopAccess.objects.filter(user=request.user,shop=current_shop,group__name="customer").exists():
            is_shop_customer = True

        if ShopAccess.objects.filter(user=request.user,shop=current_shop,group__name="vendor").exists():
            is_shop_vendor = True
            
        if ShopAccess.objects.filter(user=request.user,shop=current_shop,group__name="distributor").exists():
            is_shop_distributor = True

    current_role = "user"

    if "current_role" in request.session:
        role =  request.session['current_role']
        if role == "administrator" and is_shop_superadmin:
            current_role = "superadmin"
        elif role == "administrator" and is_shop_administrator:
            current_role = role
        elif role == "staff" and is_shop_staff:
            current_role = role
        elif role == "customer" and is_shop_customer:
            current_role = role
        elif role == "vendor" and is_shop_vendor:
            current_role = role
        elif role == "distributor" and is_shop_distributor:
            current_role = role
    else:
        if is_shop_superadmin:
            current_role = "superadmin"
        elif is_shop_administrator:
            current_role = "administrator"
        elif is_shop_staff:
            current_role = "staff"
        elif is_shop_customer:
            current_role = "customer"
        elif is_shop_vendor:
            current_role = "vendor"
        elif is_shop_distributor:
            current_role = "distributor"

    return current_role


def get_shops(request):
    shops = []
    if request.user.is_authenticated:
        shop_access = ShopAccess.objects.filter(user=request.user,is_accepted=True)
        for access in shop_access:
            if not access.shop in shops:
                shops.append(access.shop)

    return shops
