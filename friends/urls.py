from django.urls import path

from . import views

urlpatterns = [
    path('', views.friends_view, name='friends'),
    path('search.json', views.search_json_view, name='friends_search_json'),
    path('add/<int:user_id>/', views.add_view, name='friend_add'),
    path('accept/<int:user_id>/', views.accept_view, name='friend_accept'),
    path('remove/<int:user_id>/', views.remove_view, name='friend_remove'),
]
