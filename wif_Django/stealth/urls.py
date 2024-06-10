from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('register/', views.register),
    path('login/', views.login),
    path('about/', views.about),
    path('history/', views.history),
    path('profile/', views.profile),
    path('delete/', views.delete),
    path('logout/', views.logout),

]
