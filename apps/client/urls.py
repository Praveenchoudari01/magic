from django.urls import path
from . import views

app_name = "client"  # namespace

urlpatterns = [
    path('dashboard/', views.client_home, name='client_home'),
    #users(operators)
    path('users/', views.client_user_list, name='client_user_list'),
]