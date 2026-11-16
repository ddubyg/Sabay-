from django.urls import path
from . import views


urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('toggle-theme/', views.toggle_theme_view, name='toggle_theme'),
    path('toggle-notifications/', views.toggle_notifications_view, name='toggle_notifications'),
]
