from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from apps.accounts.models import User
from apps.product_owner.models import Client

# Create your models here.
class Department(models.Model):
    department_name = models.CharField(max_length=100)
    department_description = models.CharField(max_length=255, null=True, blank=True)

    client = models.ForeignKey("product_owner.Client", on_delete=models.CASCADE)
    created_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="departments_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="departments_updated", null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    created_ip = models.CharField(max_length=50, null=True, blank=True)
    created_browser = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'department'

    def __str__(self):
        return self.department_name

class VRDevice(models.Model):
    device_id = models.AutoField(primary_key=True)
    unique_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255)
    device_make = models.CharField(max_length=255, blank=True, null=True)
    device_model = models.CharField(max_length=255, blank=True, null=True)
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vrdevice_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vrdevice_updated')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_ip = models.CharField(max_length=50, blank=True, null=True)
    created_browser = models.CharField(max_length=100, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vr_device'
        unique_together = ('device_name', 'client')  # device_name unique per client

    def __str__(self):
        return self.device_name
    
class Process(models.Model):
    process_id = models.AutoField(primary_key=True)
    process_name = models.CharField(max_length=255)
    process_desc = models.CharField(max_length=255)
    est_process_time = models.IntegerField()
    no_of_steps = models.IntegerField()

    # Foreign Key to Client (same app)
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'processes'

    def __str__(self):
        return self.process_name