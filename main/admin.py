from django.contrib import admin
from main.models import Shop,App


class ShopAdmin(admin.ModelAdmin):
    list_display = ('auto_id','name','address','phone','email','website','logo')
admin.site.register(Shop,ShopAdmin)


class AppAdmin(admin.ModelAdmin):
    list_display = ('date_added','application')
admin.site.register(App,AppAdmin)