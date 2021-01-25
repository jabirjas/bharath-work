from django.core.management.base import BaseCommand, CommandError
from users.models import Notification
from datetime import date, timedelta

class Command(BaseCommand):

    def handle(self, *args, **options):
    	day_threshold = date.today() - timedelta(7)
        instances = Notification.objects.filter(time__date__lte=day_threshold)
        instances.delete()
	        

