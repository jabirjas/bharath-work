from django.http.response import HttpResponse
import json
from django.urls import reverse
from django.http.response import HttpResponseRedirect, HttpResponse
import json
from users.functions import get_current_shop
from users.forms import UserForm
from users.models import Notification, Permission
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from main.decorators import ajax_required,check_mode
from django.shortcuts import resolve_url, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.tokens import default_token_generator
from django.template.response import TemplateResponse
from django.forms.models import modelformset_factory
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from users.models import Notification,UserActivity
from main.forms import ShopForm
from main.models import Shop,ShopAccess
from staffs.models import Staff
from finance.models import CashAccount
from products.models import Measurement
from main.functions import get_auto_id,get_a_id,generate_form_errors
from users.functions import get_current_shop
from main.decorators import check_mode, shop_required, check_account_balance,permissions_required,ajax_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q


@check_mode
@login_required
def dashboard(request):
    return HttpResponseRedirect(reverse('app'))


@check_mode
@login_required
def view(request,pk):
    instance = get_object_or_404(User.objects.filter(username=pk))
    context = {
        "title" : "User : " + instance.username,
        "instance" : instance,
        
        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request, 'users/user.html', context)


@check_mode
@login_required
@ajax_required
@require_GET
def check_notification(request):
    current_shop = get_current_shop(request)
    user = request.user
    count = Notification.objects.filter(user=user,is_read=False,is_active=True,shop=current_shop).count()
    return HttpResponse(json.dumps(count), content_type='application/javascript')


@check_mode
@login_required
def notifications(request):
    title = "Notifications"
    current_shop = get_current_shop(request)
    instances = Notification.objects.filter(user=request.user,is_deleted=False,is_active=True,shop=current_shop)

    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(subject__name__icontains=query) | Q(product__name__icontains=query))
        title = "Notifications - %s" %query

    context = {
        'title' : title,
        "instances" : instances,
        "is_need_select_picker": True,
        "is_need_popup_box" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request,"users/notifications.html",context)


@check_mode
@login_required
def delete_notification(request,pk):
    Notification.objects.filter(pk=pk,user=request.user).update(is_deleted=True,is_read=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Notification Successfully Deleted.",
        "redirect" : "true",
        "redirect_url" : reverse('users:notifications')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def delete_selected_notifications(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Notification.objects.filter(pk=pk,user=request.user).update(is_deleted=True,is_read=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Notification(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('users:notifications')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def read_selected_notifications(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Notification.objects.filter(pk=pk,user=request.user).update(is_deleted=True,is_read=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully marked as read",
            "message" : "Selected notification(s) successfully marked as read.",
            "redirect" : "true",
            "redirect_url" : reverse('users:notifications')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def read_notification(request,pk):
    Notification.objects.filter(pk=pk,user=request.user).update(is_read=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully marked as read",
        "message" : "Notification successfully marked as read.",
        "redirect" : "true",
        "redirect_url" : reverse('users:notifications')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@require_GET
def set_user_timezone(request):
    timezone = request.GET.get('timezone')
    request.session["set_user_timezone"] = timezone
    response_data = {}
    response_data['status'] = 'true'
    response_data['title'] = "Success"
    response_data['message'] = 'user timezone set successfully.'
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
def settings(request):
    current_shop = get_current_shop(request)
    shop_form = ShopForm(instance=current_shop)
        
    if not Measurement.objects.filter(code="BOX",unit_type='box',unit_name='box',is_deleted=False).exists():    
        Measurement(code='BOX',
            unit_type='box',
            unit_name='box',
            is_base=True,
            conversion_factor=0.0,
            is_system_generated=True,
            shop=current_shop,
            auto_id=get_auto_id(Measurement),
            a_id=get_a_id(Measurement,request),
            creator=request.user,
            updator=request.user
        ).save()

    active_menu = "shop"
    q = request.GET.get('active')
    if q:
        active_menu = q

    context = {
        "title" : "Settings",
        "shop_form" : shop_form,
        "active_menu" : active_menu,
        "is_need_select_picker" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_chosen_select" : True,
        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        "is_need_animations": True,
    }
    return render(request,"users/settings.html",context)


@require_POST
@check_mode
@login_required
def update_shop(request):
    current_shop = get_current_shop(request)
    form = ShopForm(request.POST,request.FILES,instance=current_shop)
    #printform.errors
    if form.is_valid():

        #update shop

        form.save()

        return HttpResponseRedirect(reverse("users:settings"))

    else:
        shop_form = ShopForm(instance=current_shop)

        active_menu = "shop"
        q = request.GET.get('active')
        if q:
            active_menu = q

        context = {
            "title" : "Settings",
            "shop_form" : shop_form,
            "active_menu" : active_menu,
            "is_need_select_picker" : True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_select_picker": True,
            "is_need_datetime_picker" : True
        }
        return render(request,"users/settings.html",context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_create_user'])
def create_user(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Staff.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    if request.method == "POST":
        form = UserForm(request.POST)
        response_data = {}
        message = ""
        data = []
        emails = request.POST.get('email')
        username = request.POST.get('username')
        email = str(emails)
        error = False
        if User.objects.filter(email=email).exists():
            error = True
            message += "This email already exists."

        if not error:
            if form.is_valid():
                data = form.save(commit=False)
                data.email = email
                data.is_staff = True
                data.save()
                Staff.objects.filter(pk=pk,is_deleted=False).update(user=data)
                instance = Staff.objects.get(pk=pk)

                #save permissions
                permissions = request.POST.getlist('permission')
                for perm in permissions:
                    p = Permission.objects.get(id=perm)
                    instance.permissions.add(p)

                #create shop access
                group = Group.objects.get(name="staff")
                is_default= True
                if ShopAccess.objects.filter(user=data).exists():
                    is_default = False
                ShopAccess(user=data,shop=current_shop,group=group,is_accepted=True,is_default=is_default).save()

                response_data = {
                    'status' : 'true',
                    'title' : "User Created",
                    'redirect' : 'true',
                    'redirect_url' : reverse('staffs:staffs'),
                    'message' : "User Created Successfully"
                }

            else:
                error = True
                message = ''
                # message += generate_form_errors(form,formset=False)
                print(form.errors)
                response_data = {
                    'status' : 'false',
                    'stable' : 'true',
                    'title' : "Form validation error",
                    "message" : message
                }

        else:
            response_data = {
                'status' : 'false',
                'title' : "Can't create this user",
                'redirect' : 'true',
                'redirect_url' : reverse('users:create_user', kwargs={"pk":pk}),
                'message' : message,

                "is_need_popup_box": True,
                "is_need_custom_scroll_bar": True,
                "is_need_wave_effect": True,
                "is_need_bootstrap_growl": True,
                "is_need_animations": True,
                "is_need_grid_system": True,
                "is_need_select_picker": True,
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')


    else:
        form = UserForm()
        permissions = Permission.objects.all()
        staffs_permissions = permissions.filter(app="staffs")
        customers_permissions = permissions.filter(app="customers")
        products_permissions = permissions.filter(app="products")
        sales_permissions = permissions.filter(app="sales")
        purchase_permissions = permissions.filter(app="purchases")
        vendors_permissions = permissions.filter(app="vendors")
        users_permissions = permissions.filter(app="users")
        finance_permissions = permissions.filter(app="finance")
        distributors_permissions = permissions.filter(app="distributors")
        tasks_permissions = permissions.filter(app="tasks")
        reports_permissions = permissions.filter(app="reports")
        context = {
            "form" : form,
            "title" : "Create User",
            "permissions":permissions,
            "staffs_permissions" : staffs_permissions,
            "customers_permissions" : customers_permissions,
            "products_permissions" : products_permissions,
            "sales_permissions" : sales_permissions,
            "purchase_permissions" : purchase_permissions,
            "vendors_permissions" : vendors_permissions,
            "users_permissions" : users_permissions,
            "finance_permissions" : finance_permissions,
            "distributors_permissions" : distributors_permissions,
            "tasks_permissions" : tasks_permissions,
            "reports_permissions" : reports_permissions,

            "is_need_select_picker": True,
            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_grid_system": True,

        }
        return render(request, 'users/create_user.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_change_user_permissions'])
def change_permissions(request,pk):
    response_data = {}

    instance = get_object_or_404(Staff.objects.filter(user__pk=pk))

    if request.method == "POST":

        #save permissions
        instance.permissions.clear()
        permissions = request.POST.getlist('permission')
        for perm in permissions:
            p = Permission.objects.get(id=perm)
            instance.permissions.add(p)

        response_data = {
            'status' : 'true',
            'title' : "Permission Changed",
            'redirect' : 'true',
            'redirect_url' : reverse('users:view_user', kwargs = {'pk' : pk}),
            'message' : "Permissions Successfully Changed.",

            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_select_picker": True,
        }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        permissions = Permission.objects.all()
        staff_permissions = instance.permissions.all()

        customers_permissions = permissions.filter(app="customers")
        vendors_permissions = permissions.filter(app="vendors")
        staffs_permissions = permissions.filter(app="staffs")
        users_permissions = permissions.filter(app="users")
        sales_permissions = permissions.filter(app="sales")
        purchase_permissions = permissions.filter(app="purchases")
        products_permissions = permissions.filter(app="products")
        finance_permissions = permissions.filter(app="finance")
        distributors_permissions = permissions.filter(app="distributors")
        tasks_permissions = permissions.filter(app="tasks")
        reports_permissions = permissions.filter(app="reports")

        context = {
            "title" : "Change Permissions : " + instance.first_name,
            "instance" : instance,
            "title" : "Change Permissions",

            "staff_permissions" : staff_permissions,
            "customers_permissions" : customers_permissions,
            "redirect" : True,
            "staffs_permissions" : staffs_permissions,
            "users_permissions" : users_permissions,
            "sales_permissions" : sales_permissions,
            "purchase_permissions" : purchase_permissions,
            "products_permissions" : products_permissions,
            "finance_permissions" : finance_permissions,
            "vendors_permissions" : vendors_permissions,
            "distributors_permissions" : distributors_permissions,
            "tasks_permissions" : tasks_permissions,
            "reports_permissions" : reports_permissions,

            "pk" : pk,


            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_select_picker": True,
        }
        return render(request, 'users/change_permissions.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_user'])
def users(request):
    current_shop = get_current_shop(request)
    instances = User.objects.filter(is_active=True)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(username__icontains=query))
    context = {
        "title" : "Users",
        "instances" : instances,

        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_select_picker": True,
    }
    return render(request, 'users/users.html', context)


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_user'])
def view_user(request,pk):
    instance = get_object_or_404(User.objects.filter(pk=pk))
    context = {
        "title" : "User : " + instance.username,
        "instance" : instance,

        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_select_picker": True,
    }
    return render(request, 'users/user.html', context)


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_user'])
def delete_user(request,pk):
    instance=User.objects.get(pk=pk)
    User.objects.filter(pk=pk).update(is_active=False,email=instance.email+"_deleted_",username=instance.username+"_deleted_"+str(instance.id))

    response_data = {
        "status" : "true",
        "title" : "Succesfully Deleted",
        "redirect" : "true",
        "redirect_url" : reverse('users:users'),
        "message" : "User Successfully Deleted.",

        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_select_picker": True,
        "is_need_datetime_picker" : True
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@ajax_required
@login_required
@shop_required
@permissions_required(['can_delete_user'])
def delete_selected_users(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(User.objects.filter(pk=pk))
            User.objects.filter(pk=pk).update(is_active=False,username=instance.username + "_deleted_" + str(instance.id))

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected User(s) Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('users:users')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some users first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@check_mode
@login_required
@shop_required
@permissions_required(['can_change_password'])
def change_password(request,pk):
    instance = get_object_or_404(User.objects.filter(pk=pk,is_active=True))
    if request.method == "POST":
        response_data = {}
        form = PasswordChangeForm(user=instance, data=request.POST)
        if form.is_valid():
            form.save()

            response_data = {
                'status' : 'true',
                'title' : "Successfully Changed",
                'redirect' : 'false',
                'message' : "Password Successfully Changed."
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                'status' : 'false',
                'stable' : 'true',
                'title' : "Form validation error",
                "message" : message,
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        title = "Change Password"
        change_password_form = PasswordChangeForm(user=instance)
        context = {
            "change_password_form" : change_password_form,
            "title" : title,
            "instance" : instance,

            "is_need_popup_box": True,
            "is_need_custom_scroll_bar": True,
            "is_need_wave_effect": True,
            "is_need_bootstrap_growl": True,
            "is_need_animations": True,
            "is_need_grid_system": True,
            "is_need_select_picker": True,
            "is_need_datetime_picker" : True
        }
        return render(request, 'users/change_password.html', context)


@ajax_required
@login_required
def revoke_access(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Staff.objects.filter(pk=pk,is_deleted=False,shop=current_shop))

    User.objects.filter(pk=instance.user.pk).update(is_active=False,
                                                    username=instance.user.username + "_deleted"+ str(instance.user.id) ,
                                                    email=instance.user.email + "_deleted")
    #unset user
    Staff.objects.filter(pk=pk).update(user=None)

    instance.permissions.clear()

    response_data = {
        "status" : "true",
        "title" : "Access Revoked.",
        "message" : "Access Revoked Successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('staffs:staff', kwargs = {'pk' : pk})
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    

@check_mode
@login_required
def user_activities(request):
    current_shop = get_current_shop(request)
    instances = UserActivity.objects.filter(shop=current_shop,is_deleted=False)
    
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))
        
    username = request.GET.get("user")
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)        
        instances = instances.filter(user=user)
        
    title = "User Activities"
    context = {
        'title' : title,
        "instances" : instances,
        "main_class" : 'full',

        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_select_picker": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'users/user_activities.html',context) 


@check_mode
@login_required
@shop_required
@permissions_required(['can_view_user_activity'])
def user_activity(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(UserActivity.objects.filter(pk=pk,is_deleted=False,shop=current_shop))
    
    context = {
        "instance" : instance,
        "title" : "User Activity : " + instance.title,
        "single_page" : True,

        "is_need_popup_box": True,
        "is_need_custom_scroll_bar": True,
        "is_need_wave_effect": True,
        "is_need_bootstrap_growl": True,
        "is_need_animations": True,
        "is_need_grid_system": True,
        "is_need_select_picker": True,
        "is_need_datetime_picker" : True,
    }
    return render(request,'users/user_activity.html',context)
