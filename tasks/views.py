from django.shortcuts import render,get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse,HttpResponseRedirect
from tasks.forms import TaskForm,ReminderForm,AnniversaryForm,HolidayForm
from tasks.models import Task,Reminder,Anniversary,Holiday,Event
from main.models import Shop
import json
import datetime
from users.functions import create_notification
from users.models import Permission, Notification, NotificationSubject
from main.functions import get_auto_id, generate_form_errors, get_a_id
from users.functions import get_current_shop
from django.contrib.auth.decorators import login_required
from main.decorators import permissions_required
from django.utils import timezone
from datetime import date, time
import datetime
from django.db.models import Q



@login_required
@permissions_required(['can_create_task'])
def create_task(request):
    current_shop = get_current_shop(request)
    if request.method == 'POST':
        form = TaskForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Task)
            a_id = get_a_id(Task,request)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.creator = request.user
            data.updator = request.user
            data.shop = current_shop
            data.assignee = request.user
            data.save()

            create_notification(request,"task_assigned",data)   

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Task created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:tasks')
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : form.errors
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = TaskForm()

        context = {
            "title" : "Create Task",
            "form" : form,
            "is_create_page" : True,
            
            "redirect" : "true",
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_select_picker" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_select_picker" : True,
            "is_need_datetime_picker" : True,
            "is_need_grid_system" : True,
            "redirect" : True,
        }
        return render(request,'tasks/entry.html',context)

@login_required
@permissions_required(['can_view_task'])
def tasks(request):
    current_shop = get_current_shop(request)
    instances = Task.objects.filter(is_deleted=False, shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(staff__first_name=query)|Q(title__icontains=query))

    context = {
        'instances': instances,
        "title" : 'tasks',

        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_chosen_select" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "tasks" : True,
        }
    return render(request, "tasks/tasks.html", context)

@login_required
@permissions_required(['can_modify_task'])
def edit_task(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Task.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    activity_description = get_activity_description(instance,"Previous Info")
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(staff__icontains=query)|Q(title__icontains=query))

    if request.method == "POST":
        form = TaskForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()
           
            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Task updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:tasks')
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = TaskForm(instance=instance)

        context = {
            "instance" : instance,
            "title" : "Edit Task :" + instance.staff.first_name,
            "form" : form,
            "redirect" : "true",
            "url" : reverse('tasks:edit_task', kwargs={'pk':instance.pk}),
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_select_picker" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_grid_system" : True,
            "is_need_select_picker" : True,
            "is_need_datetime_picker" : True,
            "tasks" : True,
        }
        return render(request,'tasks/entry.html',context)

@login_required
@permissions_required(['can_view_task'])
def task(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Task.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(staff__icontains=query)|Q(title__icontains=query))

    context = {
        'instance': instance,
        'title':'Task',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_chosen_select" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "tasks" : True,
    }
    return render(request, "tasks/task.html", context)

@login_required
@permissions_required(['can_delete_task'])
def delete_task(request,pk):
    current_shop = get_current_shop(request)
    Task.objects.filter(pk=pk).update(is_deleted=True, shop=current_shop)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Task deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('tasks:tasks')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def delete_selected_tasks(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Task.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Task Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('tasks:tasks')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

@login_required
@permissions_required(['can_create_reminder'])
def create_reminder(request):
    current_shop = get_current_shop(request)

    if request.method == 'POST':
        form = ReminderForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Reminder)
            a_id = get_a_id(Reminder,request)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.a_id = a_id
            data.creator = request.user
            data.updator = request.user
            data.shop = current_shop
            data.save()


            create_notification(request,"reminder",data)   
            #create user activity 
            activity_description = get_activity_description(data,"Reminder Info")
            activity = UserActivity(
                shop=current_shop,
                user=request.user,
                activity_type="create",
                app="tasks",
                title = "Created a Reminder",
                description=activity_description
            )
            activity.save()
            
            send_activity_email(request,activity)

            create_notification(request,"reminders",data)   


            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Reminder created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:reminders')
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = ReminderForm()

        context = {
            "title" : "Create Reminder",
            "form" : form,
            "redirect" : "true",
            "is_need_popup_box" : True,
            "is_need_select_picker" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "tasks" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'tasks/reminder/entry.html',context)

@login_required
@permissions_required(['can_view_reminder'])
def reminders(request):
    current_shop = get_current_shop(request)
    instances = Reminder.objects.filter(is_deleted=False, shop=current_shop)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))

    context = {
        'instances': instances,
        "title" : 'reminders',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "tasks" : True,
        }
    return render(request, "tasks/reminder/reminders.html", context)

@login_required
@permissions_required(['can_modify_reminder'])
def edit_reminder(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Reminder.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    activity_description = get_activity_description(instance,"Previous Info")
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))

    if request.method == "POST":
        form = ReminderForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updator = request.user
            data.date_updated = datetime.datetime.now()
            data.save()
            
            #create user activity            
            activity_description += get_activity_description(data,"Current Info")
            activity = UserActivity(
                shop=current_shop,
                user=request.user,
                activity_type="update",
                app="tasks",
                title = "Modified a Reminder",
                description=activity_description
            )
            activity.save()

            send_activity_email(request,activity)

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Reminder updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:reminders')
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = ReminderForm(instance=instance)

        context = {
            "instance" : instance,
            "title" : "Edit Reminder :" + instance.title,
            "form" : form,
            "redirect" : "true",
            "url" : reverse('tasks:edit_reminder', kwargs={'pk':instance.pk}),
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_select_picker" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_chosen_select" : True,
            "tasks" : True,
            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request,'tasks/reminder/entry.html',context)

@login_required
@permissions_required(['can_view_reminder'])
def reminder(request,pk):
    current_shop = get_current_shop(request)
    instance = get_object_or_404(Reminder.objects.filter(pk=pk, is_deleted=False, shop=current_shop))
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(title__icontains=query))

    context = {
        'instance': instance,
        'title':'Reminder',
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_select_picker" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_grid_system" : True,
        "is_need_animations" : True,
        "is_need_popup_box" : True,
        "tasks" : True,
    }
    return render(request, "tasks/reminder/reminder.html", context)

@login_required
@permissions_required(['can_delete_reminder'])
def delete_reminder(request,pk):
    current_shop = get_current_shop(request)
    Reminder.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True)

    response_data = {
        "status" : "true",
        "title" : "Successfully Deleted",
        "message" : "Reminder deleted successfully.",
        "redirect" : "true",
        "redirect_url" : reverse('tasks:reminders')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def delete_selected_reminders(request):
    current_shop = get_current_shop(request)

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Reminder.objects.filter(pk=pk, shop=current_shop).update(is_deleted=True)

        response_data = {
            "status" : "true",
            "title" : "Successfully Deleted",
            "message" : "Selected Reminder Successfully Deleted.",
            "redirect" : "true",
            "redirect_url" : reverse('tasks:reminders')
        }
    else:
        response_data = {
            "status" : "false",
            "title" : "Nothing selected",
            "message" : "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def create_anniversary(request):

    if request.method == "POST":
        form = AnniversaryForm(request.POST)
        

        if form.is_valid():
            
            #create staff
            data = form.save(commit=False)
            data.save()

            Event.objects.create(
                anniversary=data,
                date=data.date,
                note = data.note,
                shop = data.shop,
                event_category = "anniversary",
                title = "Anniversary - " + data.shop.name
            )           

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Anniversary created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:anniversary', kwargs = {'pk' : data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = AnniversaryForm()
        #printform

        context = {
            "form" : form,
            "title" : "Create Anniversary",
            "is_create_page" : True,
            "redirect":True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_animations" : True,

            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'tasks/anniversary/entry.html', context)


@login_required
@permissions_required(['can_modify_anniversary'])
def edit_anniversary(request,pk):
    current_shop = get_current_shop(request)

    instance = get_object_or_404(Anniversary.objects.filter(pk=pk))
    if request.method == "POST":
        form = AnniversaryForm(request.POST,instance=instance)

        if form.is_valid():

            #update staff
            data = form.save(commit=False)
            data.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Anniversary  updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('staffs:anniversary', kwargs = {'pk' : data.pk})
            }
        else:
            message = generate_form_errors(form,formset=False)

            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = AnniversaryForm(instance=instance)

        context = {
            "form" : form,
            "title" : "Edit Anniversary : " + str(instance.staff.name) + " - " + str(instance.date) ,
            "instance" : instance,
            "url" : reverse('tasks:edit_anniversary',kwargs={'pk':instance.pk}),
            "redirect" : True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_animations" : True,

            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'tasks/anniversary/entry.html', context)


@login_required
@permissions_required(['can_view_anniversary'])
def anniversaries(request):
    instances = Anniversary.objects.filter(is_deleted=False)
    query = request.GET.get("q")

    if query:
        instances = instances.filter(Q(name__icontains=query))
    title = "anniversaries"
    query = ""
    query = request.GET.get("q")

    context = {
        'instances': instances,
        "title" : 'anniversaries',


        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_animations" : True,

        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        }
    return render(request, "tasks/anniversary/anniversaries.html", context)

@login_required
@permissions_required(['can_view_anniversary'])
def anniversary(request,pk):
    instance = get_object_or_404(Anniversary.objects.filter(pk=pk,is_deleted=False))
    context = {
        "instance" : instance,
        "title" : "Anniversary  : " + str(instance.shop.name) ,
        "single_page" : True ,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_animations" : True,

        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request, 'tasks/anniversary/anniversary.html', context)


@login_required
@permissions_required(['can_delete_anniversary'])
def delete_anniversary (request,pk):
    instance = get_object_or_404(Anniversary.objects.filter(pk=pk,is_deleted=False))

    Anniversary.objects.filter(pk=pk,is_deleted=False).update(is_deleted=True)
    Event.objects.filter(anniversary=instance,is_deleted=False).update(is_deleted=True)
    response_data = {
                "status" : "true",
                "title" : "Successfully Deleted",
                "message" : "Anniversary Successfully Deleted.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:anniversaries')
            }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@permissions_required(['can_delete_anniversary'])
def delete_selected_anniversaries(request):

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Anniversary.objects.filter(
                pk=pk, is_deleted=False))
            Anniversary.objects.filter(pk=pk).update(is_deleted=True,staff=instance.staff)
            Event.objects.filter(anniversary=instance,is_deleted=False).update(is_deleted=True)
        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Anniversary Successfully Deleted.",
            "redirect": "true",


            "redirect_url": reverse('tasks:anniversaries')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



def create_holiday(request): 
    current_shop = get_current_shop(request)
    
    if request.method == "POST":
        form = HolidayForm(request.POST)
        
        if form.is_valid(): 
            auto_id = get_auto_id(Holiday)
            a_id = get_a_id(Holiday, request)            
            #create staff
            data = form.save(commit=False)
            data.creator = request.user
            data.updator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.save()  

            Event.objects.create(
                holiday=data,
                date=data.date,
                note = data.note,
                shop = current_shop,
                event_category = "holiday",
                title = "Holiday - " + data.holiday_category
            )            
            
            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Holiday created successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:holiday', kwargs = {'pk' : data.pk})
            }   
        else:            
            message = generate_form_errors(form,formset=False)     
                  
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }       
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = HolidayForm()
            
        context = {
            "form" : form,
            "title" : "Create Holiday",
            "is_create_page" : True,
            "redirect":True,

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_animations" : True,

            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'tasks/holiday/entry.html', context)


def edit_holiday(request,pk): 
    instance = get_object_or_404(Holiday.objects.filter(pk=pk))
    if request.method == "POST":
        form = HolidayForm(request.POST,instance=instance)
        
        if form.is_valid(): 
                        
            #create staff
            auto_id = get_auto_id(Holiday)
            a_id = get_a_id(Holiday, request)
            data = form.save(commit=False)
            data.updator = request.user
            data.creator = request.user
            data.auto_id = auto_id
            data.a_id = a_id
            data.shop = current_shop
            data.date_updated = datetime.datetime.now()
            data.save()              
            
            response_data = {
                "status" : "true",
                "title" : "Successfully Updated",
                "message" : "Holiday updated successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('tasks:holiday', kwargs = {'pk' : data.pk})
            }   
        else:            
            message = generate_form_errors(form,formset=False)     
                  
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : message
            }       
            
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else: 
        form = HolidayForm(instance=instance)
            
        context = {
            "form" : form,
            "title" : "Edit Holiday : " + str(instance.date),
            "instance" : instance,
            "redirect" : True,
            "url" : reverse('staffs:edit_holiday',kwargs={'pk':instance.pk}),

            "is_need_select_picker" : True,
            "is_need_popup_box" : True,
            "is_need_custom_scroll_bar" : True,
            "is_need_wave_effect" : True,
            "is_need_bootstrap_growl" : True,
            "is_need_animations" : True,

            "is_need_grid_system" : True,
            "is_need_datetime_picker" : True,
        }
        return render(request, 'staffs/holiday/entry.html', context)



def holidays(request):
    instances = Holiday.objects.filter(is_deleted=False)
    query = request.GET.get("q")

    if query:
        instances = instances.filter(Q(name__icontains=query))
    title = "holidays"
    query = ""
    query = request.GET.get("q")

    context = {
        'instances': instances,
        "title" : 'holidays',


        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_animations" : True,

        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        }
    return render(request, "tasks/holiday/holidays.html", context)



def holiday(request,pk):
    instance = get_object_or_404(Holiday.objects.filter(pk=pk,is_deleted=False))
    context = {
        "instance" : instance,
        "title" : "Holiday : " + str(instance.date),
        "single_page" : True,

        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_animations" : True,

        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
    }
    return render(request, 'tasks/holiday/holiday.html', context)

@login_required
@permissions_required(['can_delete_holiday'])
def delete_holiday(request,pk):
    instance = get_objects_or_404(Holiday.objects.filter(pk=pk,is_deleted=False))
    Holiday.objects.filter(pk=pk,is_deleted=False).update(is_deleted=True)

    Event.objects.filter(holiday=instance,is_deleted=False).update(is_deleted=True)
    response_data = {
                "status" : "true",
                "title" : "Successfully Deleted",
                "message" : "Holiday Successfully Deleted.",
                "redirect" : "true",
                "redirect_url" : reverse('staffs:holidays')
            }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

@login_required
@permissions_required(['can_delete_holiday'])
def delete_selected_holidays(request):

    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Holiday.objects.filter(
                pk=pk, is_deleted=False))
            Holiday.objects.filter(pk=pk).update(is_deleted=True)
            Event.objects.filter(holiday=instance,is_deleted=False).update(is_deleted=True)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Holiday Successfully Deleted.",
            "redirect": "true",


            "redirect_url": reverse('staffs:holidays')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@login_required
def events(request):
    instances = Event.objects.filter(is_deleted=False)
    query = request.GET.get("q")

    if query:
        instances = instances.filter(Q(name__icontains=query))
    title = "holidays"
    query = ""
    query = request.GET.get("q")

    context = {
        'instances': instances,
        "title" : 'holidays',

        'is_need_calender' : True,
        "is_need_select_picker" : True,
        "is_need_popup_box" : True,
        "is_need_custom_scroll_bar" : True,
        "is_need_wave_effect" : True,
        "is_need_bootstrap_growl" : True,
        "is_need_animations" : True,

        "is_need_grid_system" : True,
        "is_need_datetime_picker" : True,
        }
    return render(request, "tasks/events.html", context)