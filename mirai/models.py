from django.db import models
import datetime


class IaaS(models.Model):
    iaas_name = models.CharField(max_length=120)
    iaas_ip = models.GenericIPAddressField(unique=True)
    iaas_state = models.BooleanField(default=False)
    iaas_configuration = models.BooleanField(default=False)
    iaas_date_discovery = models.DateTimeField(default=datetime.datetime.now)
    iaas_date_configuration = models.DateTimeField(
        default=datetime.datetime.now)
    iaas_owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)


class IaaSConsumption(models.Model):
    iaas = models.ForeignKey(
        IaaS, related_name='consumptions', on_delete=models.SET_NULL, null=True)
    iaas_ram = models.IntegerField()
    iaas_disk = models.FloatField()
    iaas_cpu = models.IntegerField()
    iaas_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ['-iaas_time']


class IaaSPerformance(models.Model):
    iaas_source = models.ForeignKey(IaaS, related_name='iaas_source', on_delete=models.SET_NULL, null=True)
    iaas_destination = models.ForeignKey(IaaS, related_name='iaas_destination', on_delete=models.SET_NULL, null=True)
    bytes_transmitted = models.BigIntegerField(null=True)
    bits_s = models.FloatField(null=True)
    megabits_s = models.FloatField(null=True)
    megabytes_s = models.FloatField(null=True)


class Container(models.Model):
    iaas = models.ForeignKey(IaaS, on_delete=models.SET_NULL, null=True)
    container_name = models.TextField(max_length=120)
    cpu = models.TextField(max_length=120, default="1")
    ram = models.TextField(max_length=120, default="512M")
    application_type = models.TextField(max_length=120, default="video")
    ip_address = models.TextField(max_length=120, null=True)
    port = models.IntegerField(null=True)


class Client(models.Model):
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True)
    container_name = models.TextField(max_length=120)
    ip_address = models.TextField(max_length=120, null=True)
    port = models.IntegerField(null=True)


class Monitoring(models.Model):
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True)
    real_time = models.DateTimeField(default=datetime.datetime.now)
    cpu_data = models.IntegerField()
    ram_data = models.IntegerField()


class Triggers(models.Model):
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True)
    iaas = models.ForeignKey(IaaS, on_delete=models.CASCADE, null=True)
    trigger_type = models.TextField(max_length=120)
    trigger_action = models.TextField(max_length=120, default="api_call")
    trigger_time = models.DateTimeField(default=datetime.datetime.now)
    trigger_result = models.TextField(max_length=120, null=True)


class Log(models.Model):
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True)
    result = models.TextField(max_length=50)
    code = models.TextField(max_length=120)
    usage = models.BooleanField(default=False)

    def __str__(self):
        return "container: {} result: {} code: {}  usage: {} ".format(self.container, self.result, self.code, self.usage)
