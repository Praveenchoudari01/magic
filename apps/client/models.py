from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from apps.accounts.models import User
from apps.product_owner.models import Client
from django.utils import timezone
import uuid
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

# Create your models here.
class Department(models.Model):
    department_name = models.CharField(max_length=100, null=True, unique=True)
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

class VRDevice(ManualAutoIncrementMixin, models.Model):
    device_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)
    unique_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255)
    device_make = models.CharField(max_length=255, blank=True, null=True)
    device_model = models.CharField(max_length=255, blank=True, null=True)
    
    client = models.ForeignKey("product_owner.Client", on_delete=models.CASCADE)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name='vrdevice_created')
    updated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name='vrdevice_updated')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_ip = models.CharField(max_length=50, blank=True, null=True)
    created_browser = models.CharField(max_length=100, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vr_device'
        unique_together = ('device_name', 'client')  # device_name unique per client
        ordering = ["id"]

    def __str__(self):
        return self.device_name
    
def generate_uuid():
    return str(uuid.uuid4())
    
class Process(ManualAutoIncrementMixin, models.Model):
    process_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)
    process_name = models.CharField(max_length=255)
    process_desc = models.CharField(max_length=255)
    est_process_time = models.IntegerField()
    no_of_steps = models.IntegerField()

    # Foreign Key to Client (same app)
    client = models.ForeignKey(
        'product_owner.Client',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        db_table = 'processes'
        ordering = ["id"]

    def __str__(self):
        return self.process_name
    

class Step(ManualAutoIncrementMixin, models.Model):
    step_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    
    # Foreign Key to Process table
    process = models.ForeignKey(
        'client.Process',      # because Process exists in the same app
        on_delete=models.CASCADE
    )

    step_name = models.CharField(max_length=255)
    step_desc = models.CharField(max_length=255)
    est_step_time = models.IntegerField()
    step_sr_no = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        db_table = 'steps'
        ordering = ["id"]

    def __str__(self):
        return self.step_name
    
class StepContent(ManualAutoIncrementMixin, models.Model):
    CONTENT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
    ]

    step_content_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # Foreign Key to Step table
    step = models.ForeignKey(
        'client.Step',               # Step model exists in same app
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)
    desc = models.CharField(max_length=255)

    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'step_contents'

    def __str__(self):
        return f"{self.name} ({self.content_type})"

class StepContentDetail(ManualAutoIncrementMixin, models.Model):
    step_content_detail_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # FK to StepContent table
    step_content = models.ForeignKey(
        'client.StepContent',            # model in same app
        on_delete=models.CASCADE,
        related_name='details'
    )

    # language_id is unique
    language_id = models.CharField(max_length=10,db_column='content_language_id')

    file_url = models.CharField(max_length=255)

    # can store duration (for audio/video) or page count (pdf/text)
    duration_or_no_pages = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'step_content_details'

    # def __str__(self):
    #     return f"{self.step_content} ({self.content_type})"

class StepContentVoiceOver(ManualAutoIncrementMixin, models.Model):
    step_content_voice_over_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # FK to StepContentDetail
    step_content_detail = models.ForeignKey(
        'client.StepContentDetail',
        on_delete=models.CASCADE,
        related_name='voice_overs'
    )

    VOICE_OVER_FILE_TYPES = [
        ('audio', 'Audio'),
        ('tts', 'Text To Speech'),
    ]

    voice_over_file_type = models.CharField(
        max_length=10,
        choices=VOICE_OVER_FILE_TYPES
    )

    file_url = models.CharField(max_length=255)
    language_id = models.CharField(max_length=10)
    language = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'step_content_voice_over'
        ordering = ["id"]

    def __str__(self):
        return f"VoiceOver {self.step_content_voice_over_id} ({self.voice_over_file_type})"
    
class StepContentCaptions(ManualAutoIncrementMixin, models.Model):
    caption_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # FK to StepContentVoiceOver
    step_content_voice_over = models.ForeignKey(
        'client.StepContentDetail',
        on_delete=models.CASCADE,
        related_name='captions',
        db_column='step_content_detail_id'
    )

    file_url = models.CharField(max_length=255)

    CAPTION_FILE_TYPES = [
        ('vtt', 'WebVTT'),
        ('srt', 'SubRip'),
    ]

    caption_file_type = models.CharField(
        max_length=10,
        choices=CAPTION_FILE_TYPES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'step_content_captions'
        ordering = ["id"]

    def __str__(self):
        return f"Caption {self.caption_id} ({self.caption_file_type})"

class OperatorProcess(ManualAutoIncrementMixin, models.Model):
    operator_process_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # FK → processes table
    process = models.ForeignKey(
        'client.Process',
        on_delete=models.CASCADE,
        related_name='operator_processes'
    )

    # FK → User table (operator_id)
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='assigned_processes'
    )

    # FK → Client table
    client = models.ForeignKey(
        'product_owner.Client',
        on_delete=models.CASCADE,
        related_name='operator_processes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = 'oprator_process'   # using your exact table name
        ordering = ["id"]

    def __str__(self):
        return f"OperatorProcess {self.operator_process_id}"
    
class OperatorSession(ManualAutoIncrementMixin, models.Model):
    operator_session_id = models.BigAutoField(primary_key=True)

    # session_id (unique integer)
    session_id = models.CharField(max_length=36,unique=True,default=uuid.uuid4,editable=False)

    # FK → User
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='operator_sessions'
    )

    # FK → Processes
    process = models.ForeignKey(
        'client.Process',
        on_delete=models.CASCADE,
        related_name='process_sessions'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    total_time = models.IntegerField(null=True, blank=True)

    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('stopped', 'Stopped'),
        ('incomplete', 'Incomplete'),
        ('restart', 'Restart'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    # FK → Client
    client = models.ForeignKey(
        'product_owner.Client',
        on_delete=models.CASCADE,
        related_name='operator_sessions'
    )

    class Meta:
        db_table = 'operator_sessions'
        ordering = ["id"]

    def __str__(self):
        return f"Session {self.session_id} - {self.operator}"
    
class SessionStep(ManualAutoIncrementMixin, models.Model):
    session_step_id = models.CharField(max_length=36,primary_key=True,default=uuid.uuid4,editable=False)

    # step_session_id (unique int, auto-increment in DB)

    # FK → operator_sessions
    session = models.ForeignKey(
        'client.OperatorSession',
        to_field='session_id',          # 👈 IMPORTANT
        on_delete=models.CASCADE,
        related_name='session_steps',
        db_column='session_id',         # optional, but keeps column name clean
    )

    # FK → steps (step_id)
    step = models.ForeignKey(
        'client.Step',
        on_delete=models.CASCADE,
        related_name='step_session_steps',
        db_column='step_id',
    )

    # FK → steps (step_sr_no)
    step_sr_no = models.IntegerField()

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    time_spent_sec = models.IntegerField(null=True, blank=True)

    CONTENT_USED_CHOICES = [
        ('TRUE', 'True'),
        ('FALSE', 'False'),
    ]

    content_used = models.CharField(
        max_length=5,
        choices=CONTENT_USED_CHOICES,
        default='FALSE'
    )

    # FK → Client
    client = models.ForeignKey(
        'product_owner.Client',
        on_delete=models.CASCADE,
        related_name='session_steps'
    )

    class Meta:
        db_table = 'session_steps'
        ordering = ["id"]

    def __str__(self):
        return f"SessionStep {self.step_session_id} (Session {self.session.id})"
    
class SessionStepContentUsage(ManualAutoIncrementMixin, models.Model):
    CONTENT_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
    )
    session_step_content_id = models.BigAutoField(primary_key=True)
    usage_id = models.CharField(max_length=36,unique=True,default=uuid.uuid4,editable=False)

    step_session = models.ForeignKey(
        'client.SessionStep',
        to_field = 'session_step_id',
        on_delete=models.CASCADE,
        related_name='content_usages',
        db_column='step_session_id',
    )

    step_content = models.ForeignKey(
        'client.StepContent',
        on_delete=models.CASCADE,
        related_name='usages'
    )

    step_content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPES
    )

    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    duration = models.IntegerField(null=True, blank=True)

    language = models.CharField(max_length=10,db_column='language_id',null=True,blank=True)

    client = models.ForeignKey(
        'product_owner.Client',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "session_step_content_usage"
        ordering = ["id"]

    def __str__(self):
        return f"Usage {self.usage_id} for SessionStep {self.step_session_id}"