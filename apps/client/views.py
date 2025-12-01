from django.shortcuts import render, redirect
from django.utils import timezone
from jose import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.accounts.utils import perform_logout
from apps.product_owner.models import Client
from apps.accounts.models import User
from apps.client.models import Department
from django.contrib import messages
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime


# Create your views here.
def client_home(request):
    """Main dashboard home page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
    
    return render(request, "client/client_home.html")

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

    # handle add-user inline form (collapse form)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        address = request.POST.get("address", "").strip()
        department_id = request.POST.get("department_id")
        is_department_head = request.POST.get("is_department_head") == "True"

        if not email:
            messages.error(request, "Email is required.")
            return redirect("client:client_user_list")

        # generate random password
        raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # create user
        user = User.objects.create(
            name=name or email.split("@")[0],
            email=email,
            mobile=mobile,
            address=address,
            client=client_admin.client,
            department_id=department_id,
            type_id=3,  # client_user
            is_department_head=is_department_head,
            is_active=True,
            created_by=client_admin,
            created_at=timezone.now(),
            created_ip=request.META.get("REMOTE_ADDR"),
            created_browser=(request.META.get("HTTP_USER_AGENT") or "").split("/")[0][:100],
        )

        # set hashed password
        user.set_password(raw_password)
        user.save()

        return redirect("client:client_user_list")

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

    client_admin = User.objects.get(id=request.session["user_id"])

    users = User.objects.filter(client=client_admin.client)

    user = User.objects.all()

    # Fetch departments for dropdown
    departments = Department.objects.filter(client=client_admin.client, is_active=True)

    if request.method == "POST":
        name = request.POST.get("name").strip()
        email = request.POST.get("email").strip()
        mobile = request.POST.get("mobile").strip()
        address = request.POST.get("address").strip()
        designation = request.POST.get("designation", "").strip()
        department_id = request.POST.get("department_id")
        is_department_head = request.POST.get("is_department_head") == "yes"

        # Generate random password
        raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user without password first
        user = User.objects.create(
            name=name,
            email=email,
            mobile=mobile,
            address=address,
            designation=designation,
            client=client_admin.client,
            department_id=department_id,
            type_id=3,  # client_user
            is_department_head=is_department_head,
            is_active=True,
            created_by=client_admin,
            created_at=timezone.now(),
            created_ip=request.META.get("REMOTE_ADDR"),
            created_browser=(request.META.get('HTTP_USER_AGENT') or '').split('/')[0][:100],
        )

        # Set hashed password
        user.password = raw_password  # will be hashed automatically in save()
        user.save(update_fields=['password'])

        # Send email to the user with credentials
        subject = "Your Login Credentials"

        html_message = render_to_string("emails/client_user_credentials.html", {
            "name": user.name,
            "client_name": user.client.client_name,
            "user_email": user.email,
            "temp_password": raw_password,
            "department": user.department.department_name if user.department else "N/A",
            "designation": user.designation or "N/A",
            "site_url": settings.SITE_URL,
            "year": datetime.now().year,
        })

        plain_message = strip_tags(html_message)  # fallback for clients that don't support HTML

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )

        return redirect("client:client_user_list")  # redirect to user list page

    return render(request, "client/add_client_user.html", {"departments": departments})