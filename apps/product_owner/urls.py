from django.urls import path
from . import views

app_name = "product_owner"  # namespace

urlpatterns = [
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('client-registration/', views.dashboard_client, name='dashboard_client'),
    path('clients/add/', views.add_client, name='add_client'),
    path('implementer/', views.implementer_view, name='implementer_view'),
]