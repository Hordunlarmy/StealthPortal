from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse("Home Page")


def register(request):
    return HttpResponse("register Page")


def login(request):
    return HttpResponse("login Page")


def about(request):
    return HttpResponse("about Page")


def history(request):
    return HttpResponse("history Page")


def profile(request):
    return HttpResponse("profile Page")


def delete(request):
    return HttpResponse("delete Page")


def logout(request):
    return HttpResponse("logout Page")
