from django.urls import path
from . import views

app_name = "client"  # namespace

urlpatterns = [
    path('dashboard/', views.client_home, name='client_home'),

    #Department Urls
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.add_department, name='department_add'),
    path('departments/update/<int:pk>/', views.department_update, name='department_update'),
    path('departments/activate/<int:pk>/', views.department_activate, name='department_activate'),
    path('departments/deactivate/<int:dept_id>/', views.department_deactivate, name='department_deactivate'),

    #users(operators)
    path('users/', views.client_user_list, name='client_user_list'),
    path("users/add/", views.add_client_user, name="user_add"),
    path('users/update/<int:pk>/', views.user_update, name='user_update'),
    path('users/activate/<int:pk>/', views.user_activate, name='user_activate'),
    path('users/deactivate/<int:pk>/', views.user_deactivate, name='user_deactivate'),
]