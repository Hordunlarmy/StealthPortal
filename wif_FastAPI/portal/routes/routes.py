import os
from pathlib import Path
from typing import Annotated

from decouple import config
from fastapi import (APIRouter, Depends, FastAPI, HTTPException, Request,
                     Response)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

try:
    from StealthPortal.wif_FastAPI.portal.engine import get_db, models
    from StealthPortal.wif_FastAPI.portal.engine.forms import (
        LoginForm, RegistrationForm, UpdateProfileForm)
    from StealthPortal.wif_FastAPI.portal.security.auth import (Token,
                                                                TokenData,
                                                                current_user,
                                                                hash_passwd,
                                                                login_user,
                                                                logout_user,
                                                                verify_passwd)
    from StealthPortal.wif_FastAPI.portal.security.rsa import (
        decrypt_key, decrypt_message, generate_secret_word)

except ImportError:
    from portal.engine import get_db, models
    from portal.engine.forms import (LoginForm, RegistrationForm,
                                     UpdateProfileForm)
    from portal.security.auth import (Token, TokenData, current_user,
                                      hash_passwd, login_user, logout_user,
                                      verify_passwd)
    from portal.security.rsa import (decrypt_key, decrypt_message,
                                     generate_secret_word)


portal = APIRouter()

# Define base paths
base_path_1 = Path("StealthPortal/wif_FastAPI/portal/templates")
base_path_2 = Path("portal/templates")

if base_path_1.parent.exists():
    templates = Jinja2Templates(directory=f"{base_path_1.resolve()}")
else:
    templates = Jinja2Templates(directory=f"{base_path_2.resolve()}")

user_dependency = Annotated[TokenData, Depends(current_user)]


@portal.get("/")
async def index(request: Request, user: user_dependency):
    entry = config("entry", default="portfolio")
    if entry == "portal":
        site = config("site", default="ws://localhost:8000/")
    else:
        site = config("site", default="ws://localhost:8000/portal/")
    key_contents = config(
        "public_key",
        default="pass your public key in the " "env variable publickey",
    )
    code = generate_secret_word(5)
    access_token = request.cookies.get("test")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config_variable": site,
            "code": code,
            "title": "Home",
            "config_pubkey": key_contents,
            "current_user": user,
        },
    )


@portal.get("/about")
async def about(request: Request, user: user_dependency):
    return templates.TemplateResponse(
        "about.html",
        {"request": request, "title": "About", "current_user": user},
    )


@portal.get("/register", response_class=HTMLResponse)
async def register(request: Request, user: user_dependency):
    form = await RegistrationForm.from_formdata(request)
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "title": "Register",
            "form": form,
            "current_user": user,
        },
    )


@portal.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request, user: user_dependency, db: Session = Depends(get_db)
):
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        hashed_password = hash_passwd(form.password.data.encode("utf-8"))
        user = models.User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            print(e)

        # flash(f'Account created for {form.username.data}!', 'success')
        redirect_url = request.url_for("login")
        return RedirectResponse(url=redirect_url, status_code=303)
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "title": "Register",
            "form": form,
            "current_user": user,
        },
    )


@portal.get("/login", response_class=HTMLResponse)
async def login(request: Request, user: user_dependency):
    form = await LoginForm.from_formdata(request)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Login",
            "form": form,
            "current_user": user,
        },
    )


@portal.post("/login")
async def post_login(
    request: Request,
    response: Response,
    user: user_dependency,
    db: Session = Depends(get_db),
):
    form = await LoginForm.from_formdata(request)

    if await form.validate_on_submit():
        user = (
            db.query(models.User)
            .filter(models.User.email == form.email.data)
            .first()
        )

        next_page = request.query_params.get("next")
        next_page_red = RedirectResponse(url=next_page, status_code=303)
        normal_redirect = RedirectResponse(
            url=request.url_for("index"), status_code=303
        )
        redirect_response = next_page_red if next_page else normal_redirect
        await login_user(redirect_response, user, remember=form.remember.data)
        print("User logged in successfully, redirecting to home...")
        return redirect_response
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Login",
            "form": form,
            "current_user": user,
        },
        status_code=401,
    )


@portal.get("/logout")
async def logout(user: user_dependency, request: Request, response: Response):
    if user is None:
        redirect_url = (
            str(request.url_for("login")) + f"?next={request.url.path}"
        )
        return RedirectResponse(url=redirect_url, status_code=303)
    redirect_response = RedirectResponse(
        url=request.url_for("index"), status_code=303
    )
    await logout_user(redirect_response)
    return redirect_response


@portal.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request, user: user_dependency, db: Session = Depends(get_db)
):
    if user is None:
        redirect_url = (
            str(request.url_for("login")) + f"?next={request.url.path}"
        )
        return RedirectResponse(url=redirect_url, status_code=303)
    user_data = db.query(models.User).filter(models.User.id == user.id).first()
    form = await UpdateProfileForm.from_formdata(request)
    form.username.data = user_data.username
    form.email.data = user_data.email
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "form": form,
            "title": "Profile",
            "current_user": user,
        },
    )


@portal.post("/profile")
async def profile_post(
    request: Request, user: user_dependency, db: Session = Depends(get_db)
):
    if user is None:
        redirect_url = (
            str(request.url_for("login")) + f"?next={request.url.path}"
        )
        return RedirectResponse(url=redirect_url, status_code=303)
    profile = db.query(models.User).filter(models.User.id == user.id).first()

    form = await UpdateProfileForm.from_formdata(
        request=request, current_user=profile
    )

    if await form.validate_on_submit():
        if profile:
            profile.username = form.username.data
            profile.email = form.email.data
            try:
                db.commit()
                db.refresh(profile)
                redirect_url = request.url_for("profile")
                return RedirectResponse(url=redirect_url, status_code=303)
            except Exception as e:
                db.rollback()
                print(e)  # Consider using logging instead of print
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Profile",
            "form": form,
            "current_user": user,
        },
    )


@portal.get("/history", response_class=HTMLResponse)
async def history(
    request: Request,
    user: Annotated[TokenData, Depends(current_user)],
    db: Session = Depends(get_db),
):
    if user is None:
        redirect_url = (
            str(request.url_for("login")) + f"?next={request.url.path}"
        )
        return RedirectResponse(url=redirect_url, status_code=303)
    else:
        messages = (
            db.query(models.Message)
            .filter(models.Message.user_id == user.id)
            .all()
        )
        user_messages = {}
        for message in messages:
            decrypted_key = decrypt_key(message.key)
            decrypted_message = decrypt_message(
                message.message, decrypted_key, message.iv
            )
            user_messages[message.id] = decrypted_message
        return templates.TemplateResponse(
            "history.html",
            {
                "request": request,
                "messages": user_messages,
                "title": "History",
                "current_user": user,
            },
        )


@portal.get("/delete", response_class=HTMLResponse)
async def delete_message(
    request: Request, user: user_dependency, db: Session = Depends(get_db)
):
    return {"detail": "Deleted"}
