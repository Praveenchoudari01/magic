from django.urls import path
from . import views

app_name = "client"  # namespace

urlpatterns = [
    path('dashboard/', views.client_home, name='client_home'),
    path('profile/', views.client_profile, name='client_profile'),

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

    #VR Device Registration
    path('vr-devices/', views.vr_device_list_view, name='vr_device_list_view'),
    path('vr-devices/register/', views.vr_device_register_view, name='vr_device_register_view'),

    #Processes
    path('processes/', views.processes, name='processes'),
    path('processes/add/', views.add_process, name='add_process'),
    path('process/<int:process_id>/steps/', views.step_list, name='step_list'),
    path('process/<int:process_id>/steps/add/', views.add_step, name='add_step'),
    path("step/<int:step_id>/contents/", views.step_contents, name="step_contents"),
    path('step/<int:step_id>/content/add/', views.add_step_content, name='add_step_content'),
    path('step-content/<int:content_id>/details/',views.step_content_details,name='step_content_details'),
    path("step-content/<int:content_id>/details/add/",views.add_step_content_detail,name="add_step_content_detail"),
    path("step-content-detail/<int:detail_id>/voice-overs/",views.voice_over_list,name="voice_over_list"),
    path("step-content-detail/<int:detail_id>/captions/",views.caption_list,name="caption_list"),
    path("step-content/voice-over/<int:detail_id>/", views.add_voice_over, name="add_voice_over"),
    path("step-content/captions/<int:detail_id>/", views.add_captions, name="add_captions"),


    #operator-process
    path('operator-process/<int:process_id>/', views.operator_process_list, name='operator_process_list'),
    path("process/<int:process_id>/add-mapping/",views.add_mapping,name="add_mapping"),

]