from django.shortcuts import render,redirect
from apps.accounts.models import User, AuditTrail
from apps.product_owner.models import Client
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from jose import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.accounts.utils import perform_logout

# Create your views here.
def login(request):
    error = None  # Inline error variable for template
    success = None  # fixed typo from 'sucess' to 'success'

    if 'reset_success' in request.session:
        success = request.session.pop('reset_success')

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        print(f"🔹 Login attempt with email: {email}")  # Debug email

        # Automated email verification
        if not User.objects.filter(email=email, is_active=True).exists():
            print("❌ User does not exist or is inactive")
            error = "Email ID is not registered or inactive."
            return render(request, "accounts/login.html", {"error": error, "success": success})

        try:
            user = User.objects.get(email=email, is_active=True)
            print(f"🔹 User found: {user.name} (ID: {user.user_id}) (MAIL: {user.email})")

            if user.check_password(password):
                # Set session
                request.session['user_id'] = user.user_id
                request.session['user_name'] = user.name
                request.session['department_head'] = int(user.is_department_head)
                request.session['type_id'] = user.type_id.type_id
                role_name = user.type_id.type_name.lower() if user.type_id else None
                request.session['role_name'] = role_name
                request.session['user_email'] = user.email

                # Debug: print session info
                print("🔹 Session after login:")
                for key, value in request.session.items():
                    print(f"    {key}: {value}")

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
                # print("🔹 Audit trail created for login")

                # if user.first_login:
                #     return redirect('accounts:change_password')
                
                # 🔹 ADD JWT TOKEN CREATION HERE
                try:
                    payload = {
                        "user_id": user.user_id,
                        "email": user.email,
                        "role": role_name,
                        # "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
                    }
                    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
                except Exception as e:
                    # In case of JWT creation issue, continue normal login
                    print(f"JWT generation failed: {e}")
                    token = None

                # Redirect based on role
                print("role is", role_name)
                if role_name == "product owner":
                    # Redirect to Product Owner dashboard
                    response = redirect(reverse("product_owner:dashboard_home"))

                elif role_name == "Client":
                    # print("🔹 Redirecting to Client Admin dashboard")
                    request.session["client_name"] = user.client.client_name
                    request.session["client_id"] = user.client.client_id
                    response = redirect(reverse("client:client_home"))
                else:
                    request.session['department_id'] = user.department_id
                    request.session["client_name"] = user.client.client_name
                    request.session["client_id"] = user.client.client_id
                    # print(f"🔹 Regular user. Department ID stored in session: {user.department_id}")
                    response = redirect(reverse("user:user_home"))

                # 🔹 ADD JWT COOKIE TO RESPONSE
                if token:
                    response.set_cookie(
                        key="access_token",
                        value=token,
                        httponly=True,
                        secure=False,       # ✅ Change to True in production (HTTPS)
                        samesite="Lax"
                    )

                return response

            else:
                # print("❌ Invalid password")
                error = "Incorrect password."

        except User.DoesNotExist:
            # print("❌ User does not exist or is inactive")
            error = "Email ID is not registered or inactive."

    return render(request, "accounts/login.html")

def logout_view(request):
    perform_logout(request)
    response = redirect(reverse("accounts:login"))

    # 🔹 ADD JWT COOKIE DELETION
    response.delete_cookie("access_token")

    return response