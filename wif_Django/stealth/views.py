from decouple import config
from django.http import HttpResponse
from django.shortcuts import render

from .utils import generate_secret_word


def index(request):
    site = config('site', default="ws://localhost:8000/")
    key_contents = config('public_key', default="pass your public key in the "
                          "env variable publickey")
    code = generate_secret_word(5)
    return render(request, 'index.html', {
        "config_variable": site,
        "code": code, "title": "Home",
        "config_pubkey": key_contents, })


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
