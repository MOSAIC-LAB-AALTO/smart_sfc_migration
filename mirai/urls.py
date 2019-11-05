from django.urls import path, re_path, include
from mirai import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r'iaas', views.IaasViewSet)
router.register(r'trigger', views.TriggerViewSet)

iaas_router = routers.NestedSimpleRouter(router, r'iaas', lookup='iaas')
iaas_router.register(r'resource-consumption', views.IaasResourceConsumptionViewSet, base_name='iaas-resource-consumption')
iaas_router.register(r'container', views.ContainerViewSet, base_name='iaas-container')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(iaas_router.urls)),
    path('env-status/', views.EnvStatus.as_view(), name="env_status"),
    path('iperf/', views.Iperf.as_view(), name="iperf"),
    path('bandwidth/', views.Bandwidth.as_view(), name="bandwidth"),
    path('db/', views.DB.as_view(), name="db"),
    path('onos/', views.Onos.as_view(), name="onos"),
    re_path(r'^migrate/(?P<container_id>[0-9]+)/(to/(?P<to_iaas_id>[0-9]+)/)?$', views.Migrate.as_view(), name="migrate"),

]
