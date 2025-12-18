from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from jose import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.accounts.utils import perform_logout
from apps.product_owner.models import Client
from apps.accounts.models import User, Type
from apps.client.models import Department, VRDevice, Process, Step, StepContent, StepContentDetail,StepContentCaptions,StepContentVoiceOver, OperatorProcess
from django.contrib import messages
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import httpagentparser
import paho.mqtt.client as mqtt
import json
import time
from django.db.models import Count
import os
from urllib.parse import urlparse
import uuid
import environ
import boto3
from django.conf import settings

#AWS Importing
env = environ.Env()
AWS_BUCKET = env("AWS_BUCKET")
AWS_REGION = env("AWS_REGION")
AWS_ACCESS_KEY = env("AWS_ACCESS_KEY")
AWS_SECRET_KEY = env("AWS_SECRET_KEY")

print("bucket ", AWS_BUCKET)
print("Region ",AWS_REGION)
print("Access key", AWS_ACCESS_KEY)
print("Secret key ", AWS_SECRET_KEY)

aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
print("aws access key id is", aws_access_key_id)

#S3 bucket to upload the files.
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Create your views here.
def client_home(request):
    """Main dashboard home page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
    
    return render(request, "client/client_home.html")

def client_profile(request):
    """Profile page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    return render(request, "client/client_profile.html")

# Creating the Operator and displaying the operators list on the table
def client_user_list(request):
    # check if client_admin is logged in
    # print("user id is ", request.session["user_id"])
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    client_admin = User.objects.get(user_id=request.session["user_id"])
    # print("client_admin is ", client_admin)

    # fetch all users of the same client
    users = User.objects.filter(client=client_admin.client,  type_id=4).order_by("id")
    # print("users ",users)

    # fetch departments for dropdown
    departments = Department.objects.filter(client=client_admin.client, is_active=True)
    # print("departments ",departments)

    # render template
    return render(request, "client/users.html", {
        "users": users,
        "departments": departments,
    })

#View for creating the user 
def add_client_user(request):
    # Check if client_admin is logged in
    if "user_id" not in request.session:
        return redirect("accounts:login")

    t = Type.objects.get(pk=4)
    # print("Type id is", t.type_id)

    client_admin = User.objects.get(user_id=request.session["user_id"])
    # print("client admin from add_client_user view ",client_admin)

    users = User.objects.filter(client=client_admin.client)
    # print("users from  add_client_user view ", users)


    user = User.objects.all()

    # Fetch departments for dropdown
    departments = Department.objects.filter(client=client_admin.client, is_active=True)

    if request.method == "POST":
        name = request.POST.get("name").strip()
        email = request.POST.get("email").strip()
        mobile = request.POST.get("mobile").strip()
        operator_id = request.POST.get("operatorid").strip()
        address = request.POST.get("address").strip()
        department_id = request.POST.get("department_id")
        is_department_head = request.POST.get("is_department_head") == "yes"

        # Create user without password first
        user = User.objects.create(
            name=name,
            email=email,
            mobile=mobile,
            address=address,
            client=client_admin.client,
            department_id=department_id,
            type_id=Type.objects.get(pk=4),  
            is_department_head=is_department_head,
            operator_id = operator_id,
            is_active=True,
            created_by=client_admin,
            created_at=timezone.now(),
            created_ip=request.META.get("REMOTE_ADDR"),
            created_browser=(request.META.get('HTTP_USER_AGENT') or '').split('/')[0][:100],
        )
        # user.type_id = Type.objects.get(pk=4)
        user.save()

        return redirect("client:client_user_list")  # redirect to user list page

    return render(request, "client/add_client_user.html", {"departments": departments})

#Update existing Operator details
def user_update(request, pk):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    user = get_object_or_404(User, pk=pk)
    client_admin = User.objects.get(user_id=request.session['user_id'])
    departments = Department.objects.filter(client=client_admin.client, is_active=True)

    if request.method == "POST":
        user.name = request.POST.get('name').strip()
        user.email = request.POST.get('email').strip()
        user.mobile = request.POST.get('mobile').strip()
        user.operator_id = request.POST.get('operatorid')
        user.address = request.POST.get('address').strip()
        user.department_id = request.POST.get('department_id')
        user.is_department_head = request.POST.get('is_department_head') == 'True'
        user.save()
        return redirect("client:client_user_list")

    return render(request, "client/user_update.html", {"user": user, "departments": departments})

# Activate the Operator
def user_activate(request, pk):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save(update_fields=['is_active'])
    return redirect("client:client_user_list")

#Deactivate the Operator
def user_deactivate(request, pk):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save(update_fields=['is_active'])
    return redirect("client:client_user_list")


# Creating the department, update, activation and deactivation views to handle the department data
#Department listing page
def department_list(request):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    user = User.objects.get(user_id=request.session["user_id"])
    client = user.client
    departments = Department.objects.filter(client=client)

    return render(request, "client/department.html", {"departments": departments})

#department adding page
def add_department(request):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    user = User.objects.get(user_id=request.session["user_id"])
    print("user is ",user)
    client = user.client

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    browser_info = httpagentparser.simple_detect(user_agent)
    browser_name = browser_info[1] if len(browser_info) > 1 else "Unknown"

    if request.method == "POST":
        department_name = request.POST.get("department_name")
        department_description = request.POST.get("department_description")

        # 🔥 Check if department already exists for this client
        if Department.objects.filter(
            client=client,
            department_name__iexact=department_name
        ).exists():
            return render(
                request,
                "client/add_department.html",
                {
                    "error": f"Department '{department_name}' already exists.",
                    "department_name": department_name,
                    "department_description": department_description,
                }
            )

        # If not exists → Create
        Department.objects.create(
            department_name=department_name,
            department_description=department_description,
            client=client,
            created_by=user,
            created_at=timezone.now(),
            created_ip=request.META.get("REMOTE_ADDR"),
            created_browser=browser_name,
        )
        return redirect("client:department_list")

    return render(request, "client/add_department.html")

#Updating the existing department.
def department_update(request, pk):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        department.department_name = request.POST.get("department_name")
        department.department_description = request.POST.get("department_description")
        department.updated_by_id = request.session["user_id"]
        department.updated_at = timezone.now()
        department.save()
        return redirect("client:department_list")

    return render(request, "client/department_update.html", {"department": department})

# Deactivate Department
def department_deactivate(request, dept_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    user_id = request.session["user_id"]
    user = User.objects.get(user_id=user_id)

    department = get_object_or_404(Department, id=dept_id, client=user.client)
    department.is_active = False  # Soft delete
    department.updated_by = user
    department.updated_at = timezone.now()
    department.save()
    messages.success(request, f"Department '{department.department_name}' deactivated successfully!")
    return redirect("client:department_list")


# Activate Department
def department_activate(request, pk):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
    
    department = get_object_or_404(Department, pk=pk)
    department.is_active = True
    department.updated_by_id = request.session["user_id"]
    department.updated_at = timezone.now()
    department.save()
    return redirect("client:department_list")

# VR device Registration
# MQTT Publisher
def publish_mqtt_message(topic, payload):
    broker = "mqtt.360vista.app"
    port = 8883
    username = "mqttAdmin"
    password = "Vista#412"

    try:
        client = mqtt.Client()

        # ---- Authentication ----
        client.username_pw_set(username, password)

        # ---- If the broker requires TLS (port 8888 usually DOES) ----
        client.tls_set()  

        # ---- Connect ----
        client.connect(broker, port, 60)

        client.loop_start()

        message = json.dumps(payload)

        # ---- Publish with guaranteed delivery ----
        info = client.publish(
            topic,
            message,
            qos=1,
            retain=True
        )

        info.wait_for_publish()     # wait until broker ACKs the message

        #print("Publish return code:", info.rc)
        #print("Message published successfully to:", topic)

        time.sleep(1)  # allow loop to finish network operations

        client.loop_stop(force=False)
        client.disconnect()

    except Exception as e:
        print(f"MQTT publish error: {e}")

#Vr_Device
# VR Device List View
def vr_device_list_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('accounts:login')

    try:
        user = User.objects.get(pk=user_id)
        client = user.client
        # print("client id is ",client)
    except (User.DoesNotExist, Client.DoesNotExist):
        print("User or client not found.")
        messages.error(request, "User or client not found.")
        return redirect('client:client_home')

    devices = VRDevice.objects.filter(client=client).order_by('-created_at')
    return render(request, 'client/vr_device.html', {'devices': devices})


# VR Device Registration View
def vr_device_register_view(request):
    errors = {}
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('accounts:login')

    try:
        user = User.objects.get(pk=user_id)
        client = user.client

    except (User.DoesNotExist, Client.DoesNotExist):
        messages.error(request, "User or client not found.")
        return redirect('client:client_home')

    if request.method == 'POST':
        device_name = request.POST.get('device_name')
        unique_code = request.POST.get('unique_code')
        device_model = request.POST.get('device_model')
        device_make = request.POST.get('device_make')

        # Validation
        if VRDevice.objects.filter(unique_id=unique_code).exists():
            errors['unique_code'] = "This unique code already exists. Please get a new code."
        if VRDevice.objects.filter(device_name=device_name, client=client).exists():
            errors['device_name'] = "Device name already exists for this client."

        # Save VRDevice if no errors
        if not errors:
            vrdevice = VRDevice.objects.create(
                device_name=device_name,
                unique_id=unique_code,
                device_model=device_model,
                device_make=device_make,
                client=client,
                created_by=user,
                updated_by=user,
                created_ip=get_client_ip(request),
                created_browser=(request.META.get('HTTP_USER_AGENT') or '').split('/')[0][:100],
            )
            
            client_name = client.client_name
            client_id = client.client_id
            print(f"client id is {client_id} and client name is {client_name}")
            payload = {
                "status": "success",
                "message": "Device registered successfully",
                "device_id": str(vrdevice.device_id),
                "device_name": vrdevice.device_name,
                "unique_code" : vrdevice.unique_id,
                "client_id": str(client_id),
                "client_name": client_name
            }
            code = vrdevice.unique_id
            topic = f"magic/vr_devices/register/{code}"  # include unique code in topic
            publish_mqtt_message(topic, payload)
            vrdevice.save()
            messages.success(request, "VR Device registered successfully!")
            return redirect('client:vr_device_list_view')

    return render(request, 'client/vr_device_register.html', {
        'errors': errors
    })

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def vr_device_update(request, device_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    device = get_object_or_404(VRDevice, pk=device_id)
    if request.method == 'POST':
        device.device_name = request.POST.get('device_name')
        # device.unique_code = request.POST.get('unique_code')  # also allow updating unique code
        device.device_model = request.POST.get('device_model')
        device.device_make = request.POST.get('device_make')
        device.save()
        messages.success(request, "VR Device updated successfully!")
        return redirect('client:vr_device_register_view')  # <-- fixed with namespace
    return render(request, 'client/vr_device_update.html', {'device': device})

def vr_device_activate(request, device_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    device = get_object_or_404(VRDevice, pk=device_id)
    device.is_active = True
    device.save()
    messages.success(request, "VR Device activated successfully!")
    return redirect('client:vr_device_list_view')

def vr_device_deactivate(request, device_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    device = get_object_or_404(VRDevice, pk=device_id)
    device.is_active = False
    device.save()
    messages.success(request, "VR Device deactivated successfully!")
    return redirect('client:vr_device_list_view')

# Process Defining
def processes(request):
    # Check login
    if "user_id" not in request.session:
        return redirect("accounts:login")

    # Get logged-in user
    user_id = request.session["user_id"]

    # Get user's client_id directly
    client_id = User.objects.get(user_id=user_id).client_id

    # Fetch processes for this client
    processes_list = (
        Process.objects
        .filter(client_id=client_id)
        .annotate(operators=Count('operator_processes')).order_by('id')  # <-- Key: operators
    )

    context = {
        "processes": processes_list
    }

    return render(request, "client/process/processes.html", context)

# Registering the process.
def add_process(request):
    # Ensure user logged in
    if "user_id" not in request.session:
        return redirect("accounts:login")

    # Get logged-in user
    user_id = request.session["user_id"]
    user = User.objects.get(user_id=user_id)
    client_id = user.client_id

    if request.method == "POST":
        process_name = request.POST.get("process_name").strip()
        process_desc = request.POST.get("process_desc").strip()
        est_process_time = request.POST.get("est_process_time")
        no_of_steps = request.POST.get("no_of_steps")

        # Create Process
        Process.objects.create(
            process_name=process_name,
            process_desc=process_desc,
            est_process_time=est_process_time,
            no_of_steps=no_of_steps,
            client_id=client_id
        )

        messages.success(request, "Process registered successfully!")
        return redirect("client:processes")

    return render(request, "client/process/process_add.html")

def update_process(request, process_id):
    # Ensure user logged in
    if "user_id" not in request.session:
        return redirect("accounts:login")
    # Fetch process (ensure ownership)
    process = get_object_or_404(
        Process,
        pk=process_id,
    )

    if request.method == "POST":
        process.process_name = request.POST.get("process_name").strip()
        process.process_desc = request.POST.get("process_desc").strip()
        process.est_process_time = request.POST.get("est_process_time")
        process.no_of_steps = request.POST.get("no_of_steps")

        # updated_at will auto-update here
        process.save()

        messages.success(request, "Process updated successfully!")
        return redirect("client:processes")

    return render(
        request,
        "client/process/update_process.html",
        {"process": process}
    )

# Deactivate Process
def deactivate_process(request, process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    process = get_object_or_404(
        Process,
        pk=process_id
    )
    process.is_active = False
    process.save()

    messages.success(request, "Process deactivated successfully!")
    return redirect("client:processes")

# Activate Process
def activate_process(request, process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    process = get_object_or_404(
        Process,
        pk=process_id
    )

    process.is_active = True
    process.save()

    messages.success(request, "Process activated successfully!")
    return redirect("client:processes")

# Adding the Step for the Process 
def step_list(request, process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    error = None 
    success = None
    if 'error_message' in request.session:
        error = request.session.pop('error_message')
    if 'success_message' in request.session:
        success = request.session.pop('success_message')

    process = get_object_or_404(Process, pk=process_id)
    steps = Step.objects.filter(process_id=process_id).order_by('id')

    context = {
        "process": process,
        "steps": steps,
        "error_message" : error,
        "success_message" : success
    }

    return render(request, "client/process/step_list.html", context)

# Adding the step
def add_step(request, process_id):
    # Ensure user logged in
    if "user_id" not in request.session:
        return redirect("accounts:login")

    # Fetch the process
    process = get_object_or_404(Process, process_id=process_id)

    # Count existing steps for this process
    existing_steps = Step.objects.filter(process=process).count()

    # Maximum steps allowed
    allowed_steps = process.no_of_steps

    # Restriction check
    if existing_steps >= allowed_steps:
        messages.error(
            request,
            f"You have already added all {allowed_steps} steps for this process."
        )
        request.session['error_message'] = f"""You have already added all {allowed_steps} steps for this process.
                                        If you want to add more messages then please update No of steps,
                                        Or deactivate any existing step.
                                    """
        return redirect("client:step_list", process_id=process_id)

    if request.method == "POST":
        step_name = request.POST.get("step_name").strip()
        step_desc = request.POST.get("step_desc").strip()
        est_step_time = request.POST.get("est_step_time")
        step_sr_no = request.POST.get("step_sr_no")

        Step.objects.create(
            process=process,
            step_name=step_name,
            step_desc=step_desc,
            est_step_time=est_step_time,
            step_sr_no=step_sr_no,
            is_active=True
        )

        messages.success(request, "Step added successfully!")
        request.session['success_message'] = f"{step_name} added successully"
        return redirect("client:step_list", process_id=process_id)

    remaining_steps = allowed_steps - existing_steps

    return render(request, "client/process/add_step.html", {
        "process": process,
        "remaining_steps": remaining_steps,
        "allowed_steps": allowed_steps,
        "existing_steps": existing_steps,
    })

# Deactivating the step
def step_deactivation(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    print("step_id is ", step_id)
    step = get_object_or_404(
        Step,
        pk=step_id
    )
    step.is_active = False
    step.save()
    return redirect("client:step_list", process_id=step.process_id)

# Activating the step
def step_activation(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    print("step_id is ", step_id)
    step = get_object_or_404(
        Step,
        pk=step_id
    )
    step.is_active = True
    step.save()
    return redirect("client:step_list", process_id=step.process_id)

# Update Step
def update_step(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    step = get_object_or_404(
        Step,
        pk = step_id
    )
    if request.method == 'POST' :
        step.step_name = request.POST.get("step_name").strip()
        step.step_desc = request.POST.get("step_desc").strip()
        step.est_step_time = request.POST.get("est_step_time")

        step.save()
        return redirect("client:step_list", process_id=step.process_id)
    
    return render(
        request,
        "client/process/update_step.html",
        {"step": step}
    )

#Step_content
def step_contents(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    step = get_object_or_404(Step, step_id=step_id)

    # Load all contents for this step
    contents = StepContent.objects.filter(step=step).order_by('id')

    return render(request, "client/process/step_content.html", {
        "step": step,
        "contents": contents
    })

# Step content adding
def add_step_content(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    step = get_object_or_404(Step, pk=step_id)

    if request.method == "POST":
        name = request.POST.get("name")
        desc = request.POST.get("desc")
        content_type = request.POST.get("content_type")

        StepContent.objects.create(
            step=step,
            name=name,
            desc=desc,
            content_type=content_type,
            is_active=True
        )

        messages.success(request, "Content added successfully!")
        return redirect("client:step_contents", step_id)

    context = {
        "step": step,
        "content_types": StepContent.CONTENT_TYPES
    }
    return render(request, "client/process/add_step_content.html", context)

#Deactivate step_content
def deactivate_step_content(request, content_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    content = get_object_or_404(StepContent, pk=content_id)

    content.is_active = False
    content.save()
    return redirect("client:step_contents", step_id=content.step_id)

#Deactivate step_content
def activate_step_content(request, content_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    content = get_object_or_404(StepContent, pk=content_id)

    content.is_active = True
    content.save()
    return redirect("client:step_contents", step_id=content.step_id)

#Updating step content
def update_step_content(request, content_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    content = get_object_or_404(StepContent, step_content_id=content_id)

    if request.method == "POST":
        content.name = request.POST.get("name").strip()
        content.desc = request.POST.get("desc").strip()
        content.content_type = request.POST.get("content_type")

        content.save()

        messages.success(request, "Step content updated successfully.")
        return redirect("client:step_contents",step_id=content.step.step_id)

    return render(
        request,
        "client/process/update_step_content.html",
        {
            "content": content,
            "content_types": StepContent.CONTENT_TYPES
        }
    )

#Step content details
def step_content_details(request, content_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    # Get the parent StepContent
    content = get_object_or_404(StepContent, pk=content_id)
    content_type = content.get_content_type_display()

    # Get all detail rows for this StepContent
    details = StepContentDetail.objects.filter(step_content=content).order_by('-created_at')

    context = {
        "content": content,
        "details": details,
        "content_type": content_type,
    }

    return render(request, "client/process/step_content_details.html", context)

#Adding step content details
def add_step_content_detail(request, content_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    content = get_object_or_404(StepContent, pk=content_id)
    content_type = content.content_type  # VIDEO/AUDIO/PDF/IMAGE
    error = None

    if request.method == "POST":
        language_id = request.POST.get("language_id")
        duration_or_no_pages = request.POST.get("duration_or_no_pages")
        upload_file = request.FILES.get("upload_file")
        is_active = True if request.POST.get("is_active") == "on" else False

        # Basic file validation
        if not upload_file:
            error = "Please upload a file."

        else:
            ext = os.path.splitext(upload_file.name)[1].lower()

            valid_types = {
                "video": [".mp4", ".mov", ".mkv"],
                "audio": [".mp3", ".wav", ".aac"],
                "pdf":   [".pdf"],
                "document": [".pdf", ".docx"],
                "image": [".jpg", ".jpeg", ".png"],
            }

            if ext not in valid_types.get(content_type, []):
                allowed = ", ".join(valid_types.get(content_type, []))
                error = f"Invalid file type. Allowed: {allowed}"

        # Duration / Page Count validation
        if not duration_or_no_pages:
            if content_type in ["VIDEO", "AUDIO"]:
                error = "Duration required for audio/video"
            else:
                error = "Page count required"

        if error:
            return render(request, "client/process/add_step_content_detail.html", {
                "content": content,
                "error": error,
                "language_id": language_id,
                "duration_or_no_pages": duration_or_no_pages,
                "is_active": is_active,
            })

        # ---------------------------
        #  SAVE FILE TO LOCAL STORAGE
        # ---------------------------
        upload_folder = os.path.join(settings.MEDIA_ROOT, "step_content")

        os.makedirs(upload_folder, exist_ok=True)

        # create unique filename
        saved_filename = f"{content_id}_{upload_file.name}"
        saved_path = os.path.join(upload_folder, saved_filename)

        # write file to media folder manually
        with open(saved_path, "wb+") as destination:
            for chunk in upload_file.chunks():
                destination.write(chunk)

        # final URL stored in DB (MEDIA_URL + relative path)
        file_url = f"{settings.MEDIA_URL}step_content/{saved_filename}"

        # ---------------------------
        #  SAVE DB RECORD
        # ---------------------------
        StepContentDetail.objects.create(
            step_content=content,
            language_id=language_id,
            file_url=file_url,
            duration_or_no_pages=int(duration_or_no_pages),
            is_active=is_active
        )

        return redirect("client:step_content_details", content_id=content_id)

    return render(request, "client/process/add_step_content_detail.html", {
        "content": content
    })

#Deactivate step content details
def deactivate_step_content_detail(request, detail_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    detail = get_object_or_404(StepContentDetail, pk=detail_id)
    detail.is_active = False
    detail.save()
    return redirect("client:step_content_details",content_id=detail.step_content_id)

#Activate step content details
def activate_step_content_detail(request, detail_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    detail = get_object_or_404(StepContentDetail, pk=detail_id)
    detail.is_active = True
    detail.save()
    return redirect("client:step_content_details",content_id=detail.step_content_id)

def update_step_content_detail(request, detail_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    detail = get_object_or_404(StepContentDetail, pk=detail_id)
    content = detail.step_content
    content_type = content.content_type.lower()
    error = None

    if request.method == "POST":
        language_id = request.POST.get("language_id")
        duration_or_no_pages = request.POST.get("duration_or_no_pages")
        upload_file = request.FILES.get("upload_file")
        is_active = True if request.POST.get("is_active") == "on" else False

        # ---------------------------
        # FILE VALIDATION (OPTIONAL)
        # ---------------------------
        valid_types = {
            "video": [".mp4", ".mov", ".mkv"],
            "audio": [".mp3", ".wav", ".aac"],
            "pdf":   [".pdf"],
            "document": [".pdf", ".docx"],
            "image": [".jpg", ".jpeg", ".png"],
        }

        if upload_file:
            ext = os.path.splitext(upload_file.name)[1].lower()
            if ext not in valid_types.get(content_type, []):
                allowed = ", ".join(valid_types.get(content_type, []))
                error = f"Invalid file type. Allowed: {allowed}"

        # Duration / page validation
        if not duration_or_no_pages:
            if content_type in ["video", "audio"]:
                error = "Duration required for audio/video"
            else:
                error = "Page count required"

        if error:
            return render(request, "client/process/update_step_content_detail.html", {
                "content": content,
                "detail": detail,
                "error": error
            })

        # ---------------------------
        # FILE SAVE (ONLY IF NEW FILE)
        # ---------------------------
        if upload_file:
            upload_folder = os.path.join(settings.MEDIA_ROOT, "step_content")
            os.makedirs(upload_folder, exist_ok=True)

            saved_filename = f"{detail.id}_{upload_file.name}"
            saved_path = os.path.join(upload_folder, saved_filename)

            with open(saved_path, "wb+") as destination:
                for chunk in upload_file.chunks():
                    destination.write(chunk)

            detail.file_url = f"{settings.MEDIA_URL}step_content/{saved_filename}"

        # ---------------------------
        # UPDATE DB FIELDS
        # ---------------------------
        detail.language_id = language_id
        detail.duration_or_no_pages = int(duration_or_no_pages)
        detail.is_active = is_active
        detail.save()

        return redirect(
            "client:step_content_details",
            content_id=detail.step_content_id
        )

    return render(
        request,
        "client/process/update_step_content_detail.html",
        {
            "content": content,
            "detail": detail
        }
    )

def voice_over_list(request, detail_id):
    detail = get_object_or_404(StepContentDetail, pk=detail_id)
    voice_overs = StepContentVoiceOver.objects.filter(step_content_detail=detail)
    return render(request, "client/process/voice_over_list.html", {
        "detail": detail,
        "voice_overs": voice_overs,
    })

def add_voice_over(request, detail_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    detail = get_object_or_404(
        StepContentDetail,
        pk=detail_id
    )

    error = None

    languages = {
                    'EN' : 'English',
                    'TEL' : 'Telugu',
                    'HIN' : 'Hindi'
                }
    if request.method == "POST":
        language_id = request.POST.get("language_id")
        language = request.POST.get("language")  # optional display value
        # voice_over_file_type = request.POST.get("voice_over_file_type")

        upload_file = request.FILES.get("upload_file")
        voice_over_file_type = os.path.splitext(upload_file.name)[1].lower()
        language = languages[language_id] 
        # ---------------------------
        # VALIDATIONS
        # ---------------------------
        
        print(language_id)
        print(language)
        print(voice_over_file_type)
        print(upload_file)
        if not language_id:
            error = "Language is required."
        elif not voice_over_file_type:
            error = "Voice over file type is required."
        elif not upload_file:
            error = "Please upload a voice over file."

        # Validate audio file extensions
        if upload_file:
            ext = os.path.splitext(upload_file.name)[1].lower()
            print("file extention is ",ext)
            allowed_exts = [".mp3", ".wav", ".aac", ".m4a"]

            if ext not in allowed_exts:
                error = f"Invalid file format. Allowed: mp3, wav, aac, m4a and the file extension is {ext}"

        if error:
            return render(
                request,
                "client/process/add_voice_over.html",
                {
                    "detail": detail,
                    "error": error
                }
            )

        # ---------------------------
        # SAVE FILE LOCALLY
        # ---------------------------
        upload_dir = os.path.join(
            settings.MEDIA_ROOT,
            "voice_overs"
        )
        os.makedirs(upload_dir, exist_ok=True)

        # Unique filename
        filename = (
            f"{detail.id}_{language_id}_{uuid.uuid4()}"
            f"{os.path.splitext(upload_file.name)[1]}"
        )

        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb+") as destination:
            for chunk in upload_file.chunks():
                destination.write(chunk)

        file_url = f"{settings.MEDIA_URL}voice_overs/{filename}"

        # ---------------------------
        # SAVE DB RECORD
        # ---------------------------
        StepContentVoiceOver.objects.create(
            step_content_detail=detail,
            voice_over_file_type=voice_over_file_type,
            file_url=file_url,
            language_id=language_id,
            language=language,
            is_active=True
        )

        messages.success(
            request,
            "Voice over uploaded successfully!"
        )

        return redirect(
            "client:voice_over_list",
            detail_id=detail.step_content_detail_id
        )

    return render(
        request,
        "client/process/add_voice_over.html",
        {
            "detail": detail
        }
    )

def deactivate_voice_over(request, voice_over_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    voice_over = get_object_or_404(
        StepContentVoiceOver,
        step_content_voice_over_id=voice_over_id
    )

    voice_over.is_active = False
    voice_over.save(update_fields=["is_active"])

    messages.success(request, "Voice over deactivated.")

    return redirect(
        "client:voice_over_list",
        detail_id=voice_over.step_content_detail_id
    )

def activate_voice_over(request, voice_over_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    voice_over = get_object_or_404(
        StepContentVoiceOver,
        step_content_voice_over_id=voice_over_id
    )

    voice_over.is_active = True
    voice_over.save(update_fields=["is_active"])

    messages.success(request, "Voice over activated.")

    return redirect(
        "client:voice_over_list",
        detail_id=voice_over.step_content_detail_id
    )

def update_voice_over(request, voice_over_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    voice_over = get_object_or_404(
        StepContentVoiceOver,
        step_content_voice_over_id=voice_over_id
    )

    error = None

    LANGUAGE_MAP = {
        "EN": "English",
        "TEL": "Telugu",
        "HIN": "Hindi",
        "KAN": "Kannada",
        "MAL": "Malayalam",
    }

    if request.method == "POST":
        language_id = request.POST.get("language_id")
        voice_over_file_type = request.POST.get("voice_over_file_type")
        upload_file = request.FILES.get("upload_file")
        is_active = request.POST.get("is_active") == "on"

        # ---------------------------
        # VALIDATION
        # ---------------------------
        if not language_id:
            error = "Language is required."
        elif not voice_over_file_type:
            error = "Voice over file type is required."

        # Validate file only if uploaded
        if upload_file:
            ext = os.path.splitext(upload_file.name)[1].lower()
            allowed_exts = [".mp3", ".wav", ".aac", ".m4a"]

            if ext not in allowed_exts:
                error = "Invalid audio format. Allowed: mp3, wav, aac, m4a."

        if error:
            return render(
                request,
                "client/process/update_voice_over.html",
                {
                    "voice_over": voice_over,
                    "error": error
                }
            )

        # ---------------------------
        # UPDATE FILE (OPTIONAL)
        # ---------------------------
        if upload_file:
            # delete old file
            old_path = voice_over.file_url.replace(settings.MEDIA_URL, "")
            old_full_path = os.path.join(settings.MEDIA_ROOT, old_path)

            if os.path.exists(old_full_path):
                os.remove(old_full_path)

            # save new file
            upload_dir = os.path.join(settings.MEDIA_ROOT, "voice_overs")
            os.makedirs(upload_dir, exist_ok=True)

            filename = (
                f"{voice_over.step_content_detail_id}_"
                f"{language_id}_{uuid.uuid4()}"
                f"{os.path.splitext(upload_file.name)[1]}"
            )

            full_path = os.path.join(upload_dir, filename)

            with open(full_path, "wb+") as dest:
                for chunk in upload_file.chunks():
                    dest.write(chunk)

            voice_over.file_url = f"{settings.MEDIA_URL}voice_overs/{filename}"

        # ---------------------------
        # UPDATE META FIELDS (THIS WAS MISSING)
        # ---------------------------
        voice_over.language_id = language_id
        voice_over.language = LANGUAGE_MAP.get(language_id, language_id)
        voice_over.voice_over_file_type = voice_over_file_type
        voice_over.is_active = is_active

        voice_over.save()

        return redirect(
            "client:voice_over_list",
            detail_id=voice_over.step_content_detail_id
        )

    return render(
        request,
        "client/process/update_voice_over.html",
        {
            "voice_over": voice_over
        }
    )


def caption_list(request, detail_id):
    detail = get_object_or_404(StepContentDetail, pk=detail_id)

    captions = StepContentCaptions.objects.filter(
        step_content_voice_over_id=detail.step_content_detail_id
    )

    # Add filename attribute to each caption
    for c in captions:
        if c.file_url:
            filename = os.path.basename(urlparse(c.file_url).path)

            # Remove UUID (before first underscore)
            clean_name = filename.split('_', 1)[1]

            c.caption_filename = clean_name
        else:
            c.caption_filename = ""

    return render(request, "client/process/caption_list.html", {
        "detail": detail,
        "captions": captions,
    })

def add_captions(request, detail_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    detail = get_object_or_404(
        StepContentDetail,
        pk=detail_id
    )

    error = None

    # Allowed caption types
    CAPTION_TYPES = {
        "vtt": "WebVTT",
        "srt": "SubRip"
    }

    if request.method == "POST":
        caption_file_type = request.POST.get("caption_file_type")
        upload_file = request.FILES.get("upload_file")

        # ---------------------------
        # VALIDATIONS
        # ---------------------------
        if not caption_file_type:
            error = "Caption file type is required."
        elif caption_file_type not in CAPTION_TYPES:
            error = "Invalid caption file type selected."
        elif not upload_file:
            error = "Please upload a caption file."

        # Validate extension matches selected type
        if upload_file:
            ext = os.path.splitext(upload_file.name)[1].lower().replace(".", "")
            if ext != caption_file_type:
                error = (
                    f"Uploaded file type ({ext}) does not match "
                    f"selected type ({caption_file_type})."
                )

        if error:
            return render(
                request,
                "client/process/add_captions.html",
                {
                    "detail": detail,
                    "error": error
                }
            )

        # ---------------------------
        # SAVE FILE LOCALLY
        # ---------------------------
        upload_dir = os.path.join(
            settings.MEDIA_ROOT,
            "captions"
        )
        os.makedirs(upload_dir, exist_ok=True)

        filename = (
            f"{detail.id}_{uuid.uuid4()}.{caption_file_type}"
        )

        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb+") as destination:
            for chunk in upload_file.chunks():
                destination.write(chunk)

        file_url = f"{settings.MEDIA_URL}captions/{filename}"

        # ---------------------------
        # SAVE DB RECORD
        # ---------------------------
        StepContentCaptions.objects.create(
            step_content_voice_over=detail,
            caption_file_type=caption_file_type,
            file_url=file_url,
            is_active=True
        )

        messages.success(
            request,
            "Caption file uploaded successfully!"
        )

        return redirect(
            "client:caption_list",
            detail_id=detail.step_content_detail_id
        )

    return render(
        request,
        "client/process/add_captions.html",
        {
            "detail": detail
        }
    )

def deactivate_caption(request, caption_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    caption = get_object_or_404(
        StepContentCaptions,
        caption_id=caption_id
    )

    caption.is_active = False
    caption.save()

    return redirect(
        "client:caption_list",
        detail_id=caption.step_content_voice_over_id
    )

def activate_caption(request, caption_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    caption = get_object_or_404(
        StepContentCaptions,
        caption_id=caption_id
    )

    caption.is_active = True
    caption.save()

    return redirect(
        "client:caption_list",
        detail_id=caption.step_content_voice_over_id
    )

def update_caption(request, caption_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    caption = get_object_or_404(
        StepContentCaptions,
        caption_id=caption_id
    )

    detail = caption.step_content_voice_over
    error = None

    if request.method == "POST":
        caption_file_type = request.POST.get("caption_file_type")
        upload_file = request.FILES.get("upload_file")
        is_active = True if request.POST.get("is_active") == "on" else False

        if not caption_file_type:
            error = "Caption file type required."

        if upload_file:
            ext = os.path.splitext(upload_file.name)[1].lower().replace(".", "")
            print("file type ", ext)
            if ext != caption_file_type:
                error = "Uploaded file does not match selected caption type."

        if error:
            return render(
                request,
                "client/process/update_caption.html",
                {"caption": caption, "error": error}
            )

        if upload_file:
            old_path = caption.file_url.replace(settings.MEDIA_URL, "")
            old_full = os.path.join(settings.MEDIA_ROOT, old_path)
            if os.path.exists(old_full):
                os.remove(old_full)

            upload_dir = os.path.join(settings.MEDIA_ROOT, "captions")
            os.makedirs(upload_dir, exist_ok=True)

            filename = f"{detail.id}_{uuid.uuid4()}.{caption_file_type}"
            path = os.path.join(upload_dir, filename)

            with open(path, "wb+") as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

            caption.file_url = f"{settings.MEDIA_URL}captions/{filename}"

        caption.caption_file_type = caption_file_type
        caption.is_active = is_active
        caption.save()

        return redirect(
            "client:caption_list",
            detail_id=detail.step_content_detail_id
        )

    return render(
        request,
        "client/process/update_caption.html",
        {"caption": caption}
    )


def operator_process_list(request, process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    # Fetch selected process
    process = Process.objects.get(process_id=process_id)

    # # Fetch operator mappings for this process
    mappings = (
        OperatorProcess.objects
        .filter(process_id=process_id)
        .select_related('operator')
    )

    context = {
        "process": process,
        "mappings": mappings
    }

    return render(request, "client/process/operator_process.html", context)

def add_mapping(request, process_id):
    # Get process
    process = Process.objects.get(process_id=process_id)

    # Get active operators
    operators = User.objects.filter(type_id=4, is_active=True)

    if request.method == "POST":
        operator_id = request.POST.get("operator_id")
        operator = User.objects.get(user_id=operator_id)

        # Check if mapping already exists
        mapping_exists = OperatorProcess.objects.filter(
            process=process,
            operator=operator
        ).exists()

        if mapping_exists:
            # Operator already mapped -> send context message
            context = {
                "process": process,
                "mappings": OperatorProcess.objects.filter(process=process),
                "toast_message": f"Operator '{operator.name}' is already mapped with this process.",
                "toast_type": "warning",
            }
        else:
            # Create mapping
            OperatorProcess.objects.create(
                process=process,
                operator=operator,
                client=process.client
            )
            context = {
                "process": process,
                "mappings": OperatorProcess.objects.filter(process=process),
                "toast_message": f"Operator '{operator.name}' mapped successfully.",
                "toast_type": "success",
            }

        # Render the listing page directly with toast message
        return render(request, "client/process/operator_process.html", context)

    # GET request -> show add_mapping page
    return render(request, "client/process/add_mapping.html", {
        "process": process,
        "operators": operators,
    })

# Deactivation of operator-process mapping 
def deactivate_mapping(request, operator_process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    mapping = get_object_or_404(OperatorProcess, pk=operator_process_id)
    mapping.is_active = False
    mapping.save(update_fields=["is_active"])

    return redirect("client:operator_process_list", process_id = mapping.process_id)

# Activation of operator-process mapping 
def activate_mapping(request, operator_process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")
    mapping = get_object_or_404(OperatorProcess, pk=operator_process_id)
    mapping.is_active = True
    mapping.save(update_fields=["is_active"])

    return redirect("client:operator_process_list", process_id = mapping.process_id)