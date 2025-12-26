from django.http import HttpResponseForbidden
from django.shortcuts import render,redirect
from apps.accounts.models import User, AuditTrail, PasswordReset
from apps.product_owner.models import Client
from django.urls import reverse
from django.utils import timezone
from jose import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.accounts.utils import perform_logout
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_protect, csrf_exempt

# Create your views here.
@csrf_protect
def login(request):
    error = None  # Inline error variable for template
    success = None  # fixed typo from 'sucess' to 'success'

    if 'reset_success' in request.session:
        success = request.session.pop('reset_success')

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        # Automated email verification
        if not User.objects.filter(email=email, is_active=True).exists():
            error = "Invalid email or password."
            return render(request, "accounts/login.html", {"error": error, "success": success})

        try:
            user = User.objects.get(email=email, is_active=True)
            if user.check_password(password):
                # Set session
                request.session.flush() 
                request.session['user_id'] = str(user.user_id)
                request.session['user_name'] = user.name
                request.session['department_head'] = int(user.is_department_head)
                request.session['type_id'] = user.type_id.type_id
                role_name = user.type_id.type_name.lower() if user.type_id else None
                request.session['role_name'] = role_name
                request.session['user_email'] = user.email

                # Audit Trail (LOGIN)
                login = AuditTrail.objects.create(
                    user=user,
                    user_name=user.name,
                    role_name=role_name,
                    action="login",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
                    timestamp=timezone.now().astimezone()
                )
                login.save()

                if user.first_login:
                    return redirect('accounts:change_password')
                
                if role_name == "product owner":
                    response = redirect(reverse("product_owner:dashboard_home"))
                elif role_name == "client":
                    request.session["client_name"] = user.client.client_name
                    request.session["client_id"] = str(user.client.client_id)
                    response = redirect(reverse("client:client_home"))
                else:
                    return HttpResponseForbidden("Unauthorized role")

                return response

            else:
                error = "Invalid email or password."

        except User.DoesNotExist:
            error = "Invalid email or password."

    return render(request, "accounts/login.html", {"error": error, "success": success})

def logout_view(request):
    perform_logout(request)
    response = redirect(reverse("accounts:login"))

    response.delete_cookie("sessionid")

    return response

def change_password(request):
    """
    Change password view for all roles.
    Provides inline feedback instead of Django messages.
    Sends email notification after successful update.
    """
    if "user_id" not in request.session:
        return redirect("accounts:login")

    user = User.objects.get(user_id=request.session["user_id"])

    # Determine base dashboard template dynamically
    role = request.session.get("role_name", "")
    # print("role is ", role)
    if role == "product owner":
        base_template = "product_owner/base_template.html"
    elif role == "client":
        base_template = "client/client_dashboard.html"
    else :
        print("user is not having the web access")

    feedback = {}  # Dictionary to store inline messages

    if request.method == "POST":
        current_password = request.POST.get("current_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # First-login update: no current password required
        if user.first_login:
            if new_password != confirm_password:
                feedback['error'] = "New password and confirmation do not match."
            elif len(new_password) < 6:
                feedback['error'] = "Password must be at least 6 characters long."
            else:
                # Update password using your existing hashing logic
                user.password = new_password  # hashed automatically in your model
                user.first_login = False
                user.updated_at = timezone.now()
                user.save(update_fields=["password", "first_login", "updated_at"])

                # Send email notification using existing template logic
                subject = "Your Password Has Been Updated"
                html_message = render_to_string("emails/client_user_credentials.html", {
                    "name": user.name,
                    "client_name": user.client.client_name if user.type_id == 4 and user.client_id else "",
                    "user_email": user.email,
                    "temp_password": new_password,
                    "department": user.department.department_name if user.type_id == 4 and user.department_id else "N/A",
                    "designation": user.designation or "N/A",
                    "site_url": settings.SITE_URL,
                    "year": datetime.now().year,
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=html_message,
                )

                feedback['success'] = "Password updated successfully!"
                # Redirect to respective dashboard after first-login update
                if role == "product owner":
                    return redirect("product_owner:dashboard_home")
                elif role == "client":
                    return redirect("client:client_home")
                else:
                    pass

        else:
            # Normal password update
            if not user.check_password(current_password):
                feedback['error'] = "Current password is incorrect."
            elif new_password != confirm_password:
                feedback['error'] = "New password and confirmation do not match."
            elif len(new_password) < 6:
                feedback['error'] = "Password must be at least 6 characters long."
            else:
                # Update password
                user.password = new_password
                user.updated_at = timezone.now()
                user.save(update_fields=["password", "updated_at"])

                # Send email notification
                subject = "Your Password Has Been Updated"
                html_message = render_to_string("emails/client_user_credentials.html", {
                    "name": user.name,
                    "client_name": getattr(user.client, 'client_name', ''),
                    "user_email": user.email,
                    "temp_password": new_password,
                    "designation": user.designation or "N/A",
                    "site_url": settings.SITE_URL,
                    "year": datetime.now().year,
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=html_message,
                )

                feedback['success'] = "Password updated successfully!"
                # After manual update, redirect to login so they can re-login
                return redirect("accounts:login")

    return render(
        request,
        "accounts/change_password.html",
        {
            "user": user,
            "base_template": base_template,
            "role":role,
            "feedback": feedback
        }
    )

def forgot_password_view(request):
    error = None

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Create PasswordReset instance (token + OTP generated automatically)
            reset_record = PasswordReset.objects.create(user=user)

            # Build password reset link
            reset_link = request.build_absolute_uri(
                f"/reset-password/{reset_record.token}/"
            )

            # Send email with link and OTP
            send_mail(
                subject="Password Reset Request",
                message=f"Hi {user.name},\n\nClick the link below to reset your password:\n{reset_link}\n\nOTP: {reset_record.otp}\nThis link and OTP expire in 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            # ✅ Store success message in session and redirect to login page
            request.session['reset_success'] = "A password reset link has been sent to your email."
            return redirect('accounts:login')

        except User.DoesNotExist:
            error = "Email ID not registered or inactive."

    return render(request, "accounts/forgot_password.html", {"error": error})

# Updating the password via forgot password 
def reset_password_view(request, token):
    error = None
    success = None

    try:
        reset_record = PasswordReset.objects.get(token=token, used=False)
    except PasswordReset.DoesNotExist:
        return render(request, "accounts/reset_password.html", {"error": "Invalid or used link."})

    if reset_record.is_expired():
        return render(request, "accounts/reset_password.html", {"error": "This link has expired."})

    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if otp != reset_record.otp:
            error = "Invalid OTP."
        elif new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters."
        else:
            # ✅ Update password using your existing hashing logic
            user = reset_record.user
            user.password = new_password  # hashed automatically in your model
            user.first_login = False
            user.updated_at = timezone.now()
            user.save(update_fields=["password", "first_login", "updated_at"])

            # ✅ Mark token as used
            reset_record.mark_used()

            # ✅ Send acknowledgment email after successful password update
            try:
                subject = "Your Password Has Been Reset Successfully"
                message_html = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #28a745;">Password Reset Successful</h2>
                    <p>Hello <strong>{user.name}</strong>,</p>
                    <p>Your password has been successfully updated for your VB Group account.</p>
                    <p>If you did not perform this action, please contact our support team immediately.</p>
                    <br>
                    <p style="font-size: 0.9rem; color: #666;">
                      Regards,<br>
                      <strong>VB Group Security Team</strong>
                    </p>
                  </body>
                </html>
                """
                send_mail(
                    subject,
                    strip_tags(message_html),  # fallback plain text version
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message_html,
                )
            except Exception as e:
                print(f"⚠️ Email sending failed: {e}")  # Silent fail to avoid user-facing errors

            # ✅ Set a session flag for login page message
            request.session["reset_success"] = "Your password has been reset successfully."

            # ✅ Redirect to login page
            return redirect("accounts:login")

    return render(request, "accounts/reset_password.html", {"error": error, "success": success})