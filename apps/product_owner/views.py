from django.shortcuts import render, redirect,  get_object_or_404
from apps.accounts.models import User
from apps.product_owner.models import Client
from django.contrib import messages
from PIL import Image
from django.core.mail import EmailMultiAlternatives
import os
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
import random, string
from datetime import datetime
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Create your views here.
def dashboard_home(request):
    """Main dashboard home page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('accounts:login')


    # client admins (type_id = 2)
    client_admin_count = User.objects.filter(type_id=2, is_active=True).count()


    context = {
        "client_admin_count": client_admin_count,
    }
    return render(request, "product_owner/home.html", context)

def implementer_view(request):
    """Implementer page"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('accounts:login')
    
    return render(request, "product_owner/implementor.html")

def dashboard_client(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role_name")

    if not user_id:
        return redirect('accounts:login')

    # Allow only Product Owners to view client list
    if role == "product owner":
        clients = Client.objects.filter(created_by_id=user_id)
    else:
        clients = Client.objects.none()  # No access for other users

    return render(request, "product_owner/client.html", {'clients': clients})

# Helper functions
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_client_browser(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'chrome' in user_agent and 'edg' not in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        return 'Safari'
    elif 'edg' in user_agent:
        return 'Edge'
    elif 'opera' in user_agent or 'opr' in user_agent:
        return 'Opera'
    else:
        return 'Other'

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def _set_user_password(user, raw_password):
    if hasattr(user, 'set_password'):
        user.set_password(raw_password)
    elif hasattr(User, 'hash_password'):
        user.password = User.hash_password(raw_password)
    else:
        from django.contrib.auth.hashers import make_password
        user.password = make_password(raw_password)
    user.save(update_fields=['password'])

@transaction.atomic
def add_client(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    if request.method == "POST":
        user_id = request.session.get("user_id")
        po_name = request.session.get("user_name")

        client_name = request.POST.get("client_name", "").strip()
        client_urls = request.POST.get("client_urls", "").strip()
        spoc_name = request.POST.get("spoc_name", "").strip()
        spoc_email = request.POST.get("spoc_email", "").strip()
        spoc_mobile = request.POST.get("spoc_mobile", "").strip()
        client_address = request.POST.get("client_address", "").strip()
        client_logo = request.FILES.get("client_logo")

        # Validation
        if not client_name:
            messages.error(request, "Client name is required.")
            return redirect("productowner:add_client")

        if not spoc_email:
            messages.error(request, "SPOC email is required.")
            return redirect("productowner:add_client")

        # Validate logo size (30x30px only)
        if client_logo:
            try:
                img = Image.open(client_logo)
                if img.width != 30 or img.height != 30:
                    messages.error(request, "Logo must be exactly 30x30 pixels.")
                    return redirect("productowner:add_client")
            except Exception as e:
                messages.error(request, "Invalid image file for logo.")
                return redirect("productowner:add_client")

        # 1) Save client record
        client = Client.objects.create(
            client_name=client_name,
            spoc_name=spoc_name,
            spoc_email=spoc_email,
            spoc_mobile=spoc_mobile,
            client_logo=client_logo,
            client_urls=client_urls,
            client_address=client_address,
            created_by_id=user_id,
            created_ip=request.META.get("REMOTE_ADDR"),
            created_browser=(request.META.get("HTTP_USER_AGENT") or "").split("/")[0][:100],
            is_active=True,
        )

        # 2) Create SPOC user with random password
        temp_password = generate_random_password()
        spoc_user = User(
            name=spoc_name or spoc_email.split("@")[0],
            email=spoc_email,  
            mobile = spoc_mobile,
            address = client_address,
            created_ip =  request.META.get("REMOTE_ADDR"),
            created_browser=(request.META.get("HTTP_USER_AGENT") or "").split("/")[0][:100],
            is_active=True,
            type_id_id=2,
        )
        spoc_user.client_id = client.client_id
        spoc_user.save()
        _set_user_password(spoc_user, temp_password)

        client.save()

        # 3) Send mail with credentials (HTML email)
        subject = "Your Client Admin (SPOC) Login Credentials"
        context = {
            "app_name": "Akira Streaming",
            "first_name": spoc_name or "there",
            "user_email": spoc_email,
            "temp_password": temp_password,
            "set_password_link": f"{os.environ.get('SITE_URL', 'http://127.0.0.1:9090')}/login",
            "support_email": "support@akirastreaming.com",
            "year": datetime.now().year,
            "po_name": po_name,
        }

        try:
            html_content = render_to_string("email/client_credentials.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [spoc_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

        except Exception as e:
            messages.error(request, f"Failed to send email to {spoc_email}")

        messages.success(request, f"SPOC '{spoc_name}' created and credentials emailed.")
        return redirect("productowner:dashboard_client")

    return render(request, "product_owner/add_client.html")

