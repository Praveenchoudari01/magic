from django.urls import path
from . import views

app_name = "product_owner"  # namespace

urlpatterns = [
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('profile/', views.dashboard_profile, name='productowner_profile'),
    path('client-registration/', views.dashboard_client, name='dashboard_client'),
    path('clients/add/', views.add_client, name='add_client'),
    path('clients/edit/<uuid:client_id>/', views.edit_client, name='edit_client'),
    path('clients/activate/<uuid:client_id>/', views.activate_client, name='activate_client'),
    path('clients/deactivate/<uuid:client_id>/', views.deactivate_client, name='deactivate_client'),
    path('implementer/', views.implementer_view, name='implementer_view'),
    path('client-subscription/<uuid:client_id>/subscription/',views.manage_client_subscription,name='manage_client_subscription'),
]