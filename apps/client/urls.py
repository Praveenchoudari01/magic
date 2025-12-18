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
    path('users/update/<uuid:pk>/', views.user_update, name='user_update'),
    path('users/activate/<uuid:pk>/', views.user_activate, name='user_activate'),
    path('users/deactivate/<uuid:pk>/', views.user_deactivate, name='user_deactivate'),

    #VR Device Registration
    path('vr-devices/', views.vr_device_list_view, name='vr_device_list_view'),
    path('vr-devices/register/', views.vr_device_register_view, name='vr_device_register_view'),
    path('vr-device/update/<uuid:device_id>/', views.vr_device_update, name='vr_device_update'),
    path('vr-device/activate/<uuid:device_id>/', views.vr_device_activate, name='vr_device_activate'),
    path('vr-device/deactivate/<uuid:device_id>/', views.vr_device_deactivate, name='vr_device_deactivate'),

    #Processes
    path('processes/', views.processes, name='processes'),
    path('processes/add/', views.add_process, name='add_process'),
    path("process/deactivate/<uuid:process_id>/", views.deactivate_process, name="deactivate_process"),
    path("process/activate/<uuid:process_id>/", views.activate_process, name="activate_process"),
    path("process/<uuid:process_id>/update/",views.update_process,name="update_process"),

    path('process/<uuid:process_id>/steps/', views.step_list, name='step_list'),
    path('process/<uuid:process_id>/steps/add/', views.add_step, name='add_step'),
    path("step/<uuid:step_id>/contents/", views.step_contents, name="step_contents"),
    path('step/<uuid:step_id>/deactivate/', views.step_deactivation , name='step_deactivation'),
    path('step/<uuid:step_id>/activate/', views.step_activation , name='step_activation'),
    path('step/<uuid:step_id>/update/', views.update_step, name='update_step'),

    path('step/<uuid:step_id>/content/add/', views.add_step_content, name='add_step_content'),
    path('step-content/<uuid:content_id>/details/',views.step_content_details,name='step_content_details'),
    path('step-content/<uuid:content_id>/deactivate/', views.deactivate_step_content, name='deactivate_step_content'),
    path('step-content/<uuid:content_id>/activate/', views.activate_step_content, name='activate_step_content'),
    path('step-content/<uuid:content_id>/update/', views.update_step_content, name='update_step_content'),

    path("step-content/<uuid:content_id>/details/add/",views.add_step_content_detail,name="add_step_content_detail"),
    path('step-content-detail/<uuid:detail_id>/deactivate/',views.deactivate_step_content_detail, name='deactivate_step_content_detail'),
    path('step-content-detail/<uuid:detail_id>/activate/',views.activate_step_content_detail, name='activate_step_content_detail'),
    path("step-content-detail/<uuid:detail_id>/update/",views.update_step_content_detail,name="update_step_content_detail"),

    path("step-content-detail/<uuid:detail_id>/voice-overs/",views.voice_over_list,name="voice_over_list"),
    path("step-content-detail/<uuid:detail_id>/voice-overs/add/", views.add_voice_over, name="add_voice_over"),
    path("step-content-detail/voice-over/<uuid:voice_over_id>/deactivate/",views.deactivate_voice_over,name="deactivate_voice_over"),
    path("step-content-detail/voice-over/<uuid:voice_over_id>/activate/",views.activate_voice_over,name="activate_voice_over"),
    path("step-content-detail/voice-over/<uuid:voice_over_id>/update/",views.update_voice_over,name="update_voice_over"),

    path("step-content-detail/<uuid:detail_id>/captions/",views.caption_list,name="caption_list"), 
    path("step-content-detail/<uuid:detail_id>/captions/add/",views.add_captions,name="add_captions"),
    path("step-content-detail/caption/<uuid:caption_id>/deactivate/",views.deactivate_caption,name="deactivate_caption"),
    path("step-content-detail/caption/<uuid:caption_id>/activate/",views.activate_caption,name="activate_caption"),
    path("step-content-detail/caption/<uuid:caption_id>/update/",views.update_caption,name="update_caption"),

    #operator-process
    path('operator-process/<uuid:process_id>/', views.operator_process_list, name='operator_process_list'),
    path("process/<uuid:process_id>/add-mapping/",views.add_mapping,name="add_mapping"),
    path('operator-process/<uuid:operator_process_id>/deactivate/', views.deactivate_mapping, name='deactivate_mapping'),
    path('operator-process/<uuid:operator_process_id>/activate/', views.activate_mapping, name='activate_mapping'),

]