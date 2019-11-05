from django.contrib import admin
from django.urls import path, include
from mirai_project import tasks


urlpatterns = [
    path('admin/', admin.site.urls),

    # url(r'^api/container_migrate',              views.container_migrate, name="container_migrate"),
 
    # url(r'^api/trigger_status',                 views.trigger_status, name="trigger_stats"),
   
   

    path('', include('mirai.urls')),


]
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

# run daemons when django starts
"""
tasks.iaas_daemon.delay()
tasks.iaas_consumption.delay()
"""
tasks.iaas_daemon.delay()
# tasks.iaas_consumption.delay()
# tasks.iperf_test.delay()
