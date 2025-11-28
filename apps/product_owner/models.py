from django.db import models
import uuid
from django.utils import timezone

class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    client_name = models.CharField(max_length=100, unique=True)
    spoc_name = models.CharField(max_length=100, blank=True, null=True)
    spoc_email = models.CharField(max_length=100, blank=True, null=True)
    spoc_mobile = models.CharField(max_length=15, blank=True, null=True)
    client_logo = models.ImageField(upload_to="client_logos/", blank=True, null=True) #here we are taking the images 
    client_urls = models.URLField(max_length=255, blank=True, null=True) #store to client urls 
    client_address = models.CharField(max_length=255, blank=True, null=True)

    created_by = models.ForeignKey("accounts.User", related_name="clients_created", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey("accounts.User", related_name="clients_updated", on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_ip = models.CharField(max_length=50, blank=True, null=True)
    created_browser = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)


    class Meta:
        db_table = 'client'

    def __str__(self):
        return self.client_name
