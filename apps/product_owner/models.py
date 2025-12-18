from django.db import models
import uuid
from django.utils import timezone
from django.db import transaction
from django.db.models import Max

class ManualAutoIncrementMixin(models.Model):
    id = models.PositiveBigIntegerField(unique=True, null=True, editable=False)

    class Meta:
        abstract = True

    def assign_auto_id(self):
        if self.id is None:
            from django.db import transaction
            from django.db.models import Max
            with transaction.atomic():
                last_id = self.__class__.objects.select_for_update().aggregate(Max("id"))["id__max"] or 0
                self.id = last_id + 1

    def save(self, *args, **kwargs):
        self.assign_auto_id()
        super().save(*args, **kwargs)

class Client(ManualAutoIncrementMixin, models.Model):
    client_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)
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
        ordering = ["id"]

    def __str__(self):
        return self.client_name

# subscriptions/models.py
class ClientConfig(models.Model):
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    no_of_devices = models.PositiveIntegerField(default=0)
    no_of_processes = models.PositiveIntegerField(default=0)
    no_of_operators = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('SUSPENDED', 'Suspended'),
        ],
        default='ACTIVE'
    )

    created_by = models.ForeignKey("accounts.User", related_name="clients_subscription_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey("accounts.User", related_name="clients_subscription_updated", on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'client_config'

    def __str__(self):
        return f"{self.client.name} Subscription"
