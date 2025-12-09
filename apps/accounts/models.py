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
    first_login = models.BooleanField(default=True)

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
    
class AuditTrail(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="audit_trails")
    user_name = models.CharField(max_length=100)   # stored from session
    role_name = models.CharField(max_length=50)    # stored from session
    action = models.CharField(max_length=10, choices=[("login", "Login"), ("logout", "Logout")])
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)  # <--- add this

    class Meta:
        db_table = "audit_trail"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user_name} ({self.role_name}) - {self.action} at {self.timestamp}"
    
# Model to reset the passsword via forgot password link
class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
    token = models.CharField(max_length=255, unique=True, editable=False)
    otp = models.CharField(max_length=6, editable=False)
    expiry_time = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            # Generate a secure random token
            self.token = secrets.token_urlsafe(32)
        if not self.otp:
            # Generate a 6-digit OTP
            self.otp = f"{secrets.randbelow(1000000):06d}"
        if not self.expiry_time:
            # Default expiry: 10 minutes from creation
            self.expiry_time = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expiry_time

    def mark_used(self):
        self.used = True
        self.save()

    def __str__(self):
        return f"PasswordReset(user={self.user.email}, token={self.token}, used={self.used})"