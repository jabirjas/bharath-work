from mailqueue.models import MailerMessage  
from django.conf import settings
from django.contrib.auth.models import User
from users.models import NotificationSubject, Notification
from main.models import Shop, ShopAccess
from staffs.models import Staff


def send_email(to_address,subject,content,html_content,bcc_address=settings.DEFAULT_BCC_EMAIL,attachment=None,attachment2=None,attachment3=None):
    new_message = MailerMessage()
    new_message.subject = subject
    new_message.to_address = to_address
    if bcc_address:
        new_message.bcc_address = bcc_address
    new_message.from_address = settings.DEFAULT_FROM_EMAIL
    new_message.content = content
    new_message.html_content = html_content
    if attachment:
        new_message.add_attachment(attachment)
    if attachment2:
        new_message.add_attachment(attachment2)
    if attachment3:
        new_message.add_attachment(attachment3)
    new_message.app = "arkboss"
    new_message.save()
    
    
def get_name(user_id):
    name = User.objects.get(id=user_id).username
            
    return name


def get_email(user_id):
    email = User.objects.get(id=user_id).email            
    return email


def create_notification(request,notification_type,instance=False):
    current_shop = get_current_shop(request)
    who = request.user
    subject = NotificationSubject.objects.get(code=notification_type)
    superusers = User.objects.filter(is_active=True,is_superuser=True)  

    if notification_type == "payment_remainder" :
        
        #create notification for super user 
        for superuser in superusers :    
            Notification(
                user = superuser,
                subject = subject,
                who = who,
                sale = instance,
                customer = instance.customer,
                shop = current_shop
            ).save()

    if notification_type == "low_stock_notification" :
        
        #create notification for super user 
        for superuser in superusers :    
            Notification(
                user = superuser,
                subject = subject,
                who = who,
                product = instance,
                is_active = True,
                shop = current_shop
            ).save()

    if notification_type == "task_assigned" :
        #create notification for super user 
        for superuser in superusers :    
            Notification(
                user = superuser,
                subject = subject,
                who = who,
                task = instance,
                is_active = True,
                shop = current_shop
            ).save()

        staff = instance.staff 
        if staff.user:

            Notification(
                user = staff.user,
                subject = subject,
                who = who,
                task = instance,
                is_active = True,
                shop = current_shop
            ).save()

    if notification_type == "expiry_notification" :
        #create notification for super user 
        for superuser in superusers :    
            Notification(
                user = superuser,
                subject = subject,
                who = who,
                product = instance,
                is_active = True,
                shop = current_shop
            ).save()

        staffs = Staff.objects.filter(is_deleted=False)
        for staff in staffs:
            user = staff.user
            if not who == user:
                if staff.permissionlist:
                    permlist = [str(x.code) for x in staff.permissions.all()]
                    if 'can_view_product' in permlist:
                        Notification(
                            user = staff.user,
                            subject = subject,
                            who = who,
                            product = instance,
                            is_active = True,
                            shop = current_shop
                        ).save()
    

def get_current_shop(request):
    shop = None
    if request.user.is_authenticated:
        if "current_shop" in request.session:
            pk =  request.session['current_shop']
            if Shop.objects.filter(pk=pk).exists():
                shop = Shop.objects.get(pk=pk)
        elif ShopAccess.objects.filter(user=request.user,is_default=True).exists():
            shop = ShopAccess.objects.get(user=request.user,is_default=True).shop        
                    
    return shop


def shop_access(request):
    shops = []
    if request.user.is_authenticated:
        shop_access = ShopAccess.objects.filter(user=request.user,is_accepted=True)
        for access in shop_access:
            if not access.shop in shops:
                shops.append(access.shop)
        
    return shops


def get_activity_description(instance,title):
    lst = instance._meta.get_all_field_names()
    try:
        lst.remove('id')
        lst.remove('updator')
        lst.remove('creator')
        lst.remove('date_updated')
        lst.remove('date_added')
        lst.remove('updator_id')
        lst.remove('creator_id')
        lst.remove('shop_id')
        lst.remove('shop')
        lst.remove('is_deleted')
        lst.remove('user_id')
        lst.remove('user')
        lst.remove('permissions')
    except:
        pass
    strreto = '<div class="col-sm-6"><h4>' + title + '</h4><ul>'
    for f in lst:
        try:
            value = getattr(instance, f)
            if value:
                strreto += '<li><span class="lgi-heading">%s <small>:</small></span><span class="text"> %s</span></li>' %(str(f),str(value))
            else:
                strreto += '<li><span class="lgi-heading">%s <small>:</small></span><span class="text"> -</span></li>' %(str(f))
        except:
            value = ''
    strreto += '</ul></div>'
    return strreto
            


