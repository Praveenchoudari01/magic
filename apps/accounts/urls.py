from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login, name="login"),  # Home page
    path('login/', views.login, name='login'), 
    path("logout/", views.logout_view, name="logout"),
]