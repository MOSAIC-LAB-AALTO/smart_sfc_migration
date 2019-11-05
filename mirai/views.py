from dsmirai.persistent_model import dashboard_helper

from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from mirai import tasks
from mirai_project import tasks as t


from mirai.permissions import IsOwner
from mirai.models import IaaS, IaaSConsumption, Container, Triggers, Log  # TODO

from mirai.serializers import (IaaSSerializer,
                               EnvStatusSerializer,
                               IaasResourceConsumptionSerializer,
                               ContainerSerializer,
                               TriggersSerializer)

class DB(APIView):
    def get_object(self):
        a = t.db_cleaner.delay()
        return 1

    def get(self, request, format=None):
        env_status = self.get_object()
        serializer = EnvStatusSerializer(env_status)
        return Response(serializer.data)


class Bandwidth(APIView):
    def get_object(self):
        a = t.bandwidth_live_test.delay()
        return 1

    def get(self, request, format=None):
        env_status = self.get_object()
        serializer = EnvStatusSerializer(env_status)
        return Response(serializer.data)

class EnvStatus(APIView):
    """
    The dashboard page where various information on the infrastructure are displayed
    """

    def get_object(self):

        env_status = {
            "online_iaas": dashboard_helper.get_online_iaas(),
            "total_iaas": dashboard_helper.get_total_iaas(),
            "online_container": dashboard_helper.get_online_container(),
        }

        # TODO delete this when the env worked
        env_status = {
            "online_iaas": 3,
            "total_iaas": 3,
            "online_container": 3,
        }
        return env_status

    def get(self, request, format=None):
        env_status = self.get_object()
        serializer = EnvStatusSerializer(env_status)
        return Response(serializer.data)


class IaasResourceConsumptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The resource consumption of an IaaS
    """

    def get_queryset(self):
        return IaaSConsumption.objects.filter(iaas__iaas_owner=self.request.user, iaas=self.kwargs['iaas_pk'])
    queryset = IaaSConsumption.objects.none()
    serializer_class = IaasResourceConsumptionSerializer


class IaasViewSet(viewsets.ModelViewSet):
    """
    CRUD IaaS
    """

    def get_queryset(self):
        return IaaS.objects.filter(iaas_owner=self.request.user)
    queryset = IaaS.objects.none()
    serializer_class = IaaSSerializer
    permission_classes = (IsOwner,)

    def perform_create(self, serializer):
        serializer.save(iaas_owner=self.request.user)


class ContainerViewSet(viewsets.ModelViewSet):
    """
    CRUD Container
    """

    def get_queryset(self):
        iaas=self.kwargs['iaas_pk']
        return Container.objects.filter(iaas__iaas_owner=self.request.user,iaas=iaas)

    queryset = Container.objects.none()
    serializer_class = ContainerSerializer

    def perform_create(self, serializer):
        container = serializer.save()
        tasks.lxc_creation.delay(container.id)


class Migrate(APIView):
    """
    To be determined later
    """
    def valid_iaas(self):
        pass

    def valid_container(self):
        pass

    # TODO: in case of no iaas please send me None ya khal rass
    def get(self, request, container_id, to_iaas_id, format=None):
        tasks.lxc_migration.delay(container_id, to_iaas_id)
        return Response({"container": container_id, "to_iaas": to_iaas_id})

class TriggerViewSet(viewsets.ModelViewSet):
    """
    CRUD Container
    """

    def get_queryset(self):
        return Triggers.objects.filter(iaas__iaas_owner=self.request.user) | Triggers.objects.filter(iaas=None)

    queryset = Triggers.objects.none()
    serializer_class = TriggersSerializer

    def perform_create(self, serializer):
        trigger = serializer.save()
        instance = serializer.instance
        iaas = None
        if instance.iaas:
            iaas = instance.iaas.id
        if serializer.validated_data["trigger_type"] == "rat_trigger":
            print(f'RAT trigger to a specific IaaS: {iaas}')
            tasks.api_rat.delay(iaas)
        elif serializer.validated_data["trigger_type"] == "sct_trigger":
            print(f'SCT trigger to a specific IaaS: {iaas}')
            tasks.api_sct.delay(iaas)
        else:
            print('Trigger not available!!!')
