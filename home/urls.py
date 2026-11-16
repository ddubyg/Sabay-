from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_view, name='home'),
    path('create/', views.create_activity_view, name='create_activity'),
    path('activity/<int:pk>/', views.activity_detail_view, name='activity_detail'),
]
