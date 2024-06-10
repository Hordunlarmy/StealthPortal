from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('profile/', views.profile, name='profile'),
    path('delete/', views.delete, name='delete'),
    path('logout/', views.logout, name='logout'),

]
