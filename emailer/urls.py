from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    # Campaign management
    path('', views.campaign_list, name='campaign_list'),
    path('import/', views.import_recipients, name='import_recipients'),
    path('campaign/<uuid:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaign/<uuid:campaign_id>/delete/', views.delete_campaign, name='delete_campaign'),
    
    # Email sending
    path('campaign/<uuid:campaign_id>/send/', views.send_campaign_emails, name='send_campaign_emails'),
    path('recipient/<int:recipient_id>/test/', views.test_single_email, name='test_single_email'),

    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]