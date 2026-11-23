from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_view, name='home'),
    path('create/', views.create_activity_view, name='create_activity'),
    path('activity/<int:pk>/', views.activity_detail_view, name='activity_detail'),
    path('activity/<int:pk>/join/', views.join_activity_view, name='join_activity'),
    path('activity/<int:pk>/edit/', views.edit_activity_view, name='edit_activity'),
    path('activity/<int:pk>/delete/', views.delete_activity_view, name='delete_activity'),
    path('activity/<int:pk>/leave/', views.leave_activity_view, name='leave_activity'),
]
