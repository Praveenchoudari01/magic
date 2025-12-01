from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import secrets

# Create your models here.
class Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'type'

    def __str__(self):
        return self.type_name

class User(models.Model):
    user_id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    # Foreign Keys (string references to avoid circular import)
    type_id = models.ForeignKey("accounts.Type", on_delete=models.CASCADE)
    department = models.ForeignKey("client.Department", on_delete=models.CASCADE)
    client = models.ForeignKey("product_owner.Client", on_delete=models.CASCADE)

    is_department_head = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        "self",
        related_name="created_users",
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        "self",
        related_name="updated_users",
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    created_ip = models.CharField(max_length=50, null=True, blank=True)
    created_browser = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    password = models.CharField(max_length=255)

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)