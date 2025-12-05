from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from jose import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.accounts.utils import perform_logout
from apps.product_owner.models import Client
from apps.accounts.models import User, Type
from apps.client.models import Department, VRDevice, Process, Step, StepContent
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


# Create your views here.
def client_home(request):
    """Main dashboard home page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
    
    return render(request, "client/client_home.html")

# Creating the Operator and displaying the operators list on the table
def client_user_list(request):
    # check if client_admin is logged in
    print("user id is ", request.session["user_id"])
    if "user_id" not in request.session:
        return redirect("accounts:login")
    
    client_admin = User.objects.get(user_id=request.session["user_id"])
    print("client_admin is ", client_admin)

    # fetch all users of the same client
    users = User.objects.filter(client=client_admin.client).order_by("user_id")
    print("users ",users)

    # fetch departments for dropdown
    departments = Department.objects.filter(client=client_admin.client, is_active=True)
    print("departments ",departments)

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
    print("Type id is", t.type_id)

    client_admin = User.objects.get(user_id=request.session["user_id"])
    print("client admin from add_client_user view ",client_admin)

    users = User.objects.filter(client=client_admin.client)
    print("users from  add_client_user view ", users)


    user = User.objects.all()

    # Fetch departments for dropdown
    departments = Department.objects.filter(client=client_admin.client, is_active=True)

    if request.method == "POST":
        name = request.POST.get("name").strip()
        email = request.POST.get("email").strip()
        mobile = request.POST.get("mobile").strip()
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
    broker = "broker.hivemq.com"
    port = 1883

    try:
        client = mqtt.Client(callback_api_version=2)  # Updated API
        client.connect(broker, port, 60)
        client.loop_start()  # start network loop BEFORE publishing

        message = json.dumps(payload)
        result = client.publish(topic, message, qos=1)  # QoS 1 ensures delivery
        result.wait_for_publish()  # Wait until message is sent

        print("📤 Message published successfully")
        time.sleep(0.5)  # Small delay to ensure delivery
        client.loop_stop()
        client.disconnect()

    except Exception as e:
        print(f"❌ MQTT publish error: {e}")

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
            payload = {
                "status": "success",
                "message": "Device registered successfully",
                "device_id": vrdevice.device_id,
                "device_name": vrdevice.device_name,
                "unique_code" : vrdevice.unique_id,
                "client_id": client_id,
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
    processes_list = Process.objects.filter(client_id=client_id)

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

# Adding the Step for the Process 
def step_list(request, process_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    process = get_object_or_404(Process, pk=process_id)
    steps = Step.objects.filter(process_id=process_id).order_by('step_id')

    context = {
        "process": process,
        "steps": steps,
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
        return redirect("client:steps_list", process_id=process_id)

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
        return redirect("client:step_list", process_id=process_id)

    remaining_steps = allowed_steps - existing_steps

    return render(request, "client/process/add_step.html", {
        "process": process,
        "remaining_steps": remaining_steps,
        "allowed_steps": allowed_steps,
        "existing_steps": existing_steps,
    })

#Step_content
def step_contents(request, step_id):
    if "user_id" not in request.session:
        return redirect("accounts:login")

    step = get_object_or_404(Step, step_id=step_id)

    # Load all contents for this step
    contents = StepContent.objects.filter(step=step)

    return render(request, "client/process/step_content.html", {
        "step": step,
        "contents": contents
    })

