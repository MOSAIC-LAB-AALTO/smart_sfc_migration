from django.contrib import admin
from mirai.models import IaaS, IaaSConsumption, Log

# Register your models here.
admin.site.register(IaaS)
admin.site.register(IaaSConsumption)
admin.site.register(Log)
