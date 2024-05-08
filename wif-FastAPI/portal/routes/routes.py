from fastapi import (FastAPI, APIRouter, Request, HTTPException,
                     Depends, Response)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from portal.engine.forms import RegistrationForm, LoginForm, UpdateProfileForm
from portal.engine import models
from portal.engine import get_db
from sqlalchemy.orm import Session
from portal.security.auth import (TokenData, Token, login_user, current_user,
                                  logout_user, verify_passwd, hash_passwd)
from portal.security.rsa import generate_secret_word
from typing import Annotated
from fastapi.templating import Jinja2Templates


portal = APIRouter()
templates = Jinja2Templates(directory="portal/templates")
user_dependency = Annotated[TokenData, Depends(current_user)]


@portal.get("/")
async def index(request: Request, user: user_dependency):
    code = generate_secret_word(5)
    access_token = request.cookies.get("test")
    return templates.TemplateResponse(
        "index.html", {"request": request,
                       "code": code, "title": "Home",
                       "current_user": user})


@portal.get("/about")
async def about(request: Request, user: user_dependency):
    return templates.TemplateResponse("about.html", {"request": request,
                                                     "title": "About",
                                                     "current_user": user})


@portal.get("/register")
@portal.post("/register", response_class=HTMLResponse)
async def register(request: Request, user: user_dependency,
                   db: Session = Depends(get_db)):
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        hashed_password = hash_passwd(form.password.data.encode('utf-8'))
        user = models.User(username=form.username.data,
                           email=form.email.data, password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

        # flash(f'Account created for {form.username.data}!', 'success')
        return RedirectResponse(url="/")
    return templates.TemplateResponse("register.html", {"request": request,
                                                        "title": 'Register',
                                                        "form": form,
                                                        "current_user": user})


@portal.get("/login", response_class=HTMLResponse)
async def login(request: Request, user: user_dependency):
    form = await LoginForm.from_formdata(request)
    return templates.TemplateResponse("login.html",
                                      {"request": request,
                                       "title": 'Login',
                                       "form": form,
                                       "current_user": user})


@portal.post("/login")
async def post_login(request: Request, response: Response,
                     user: user_dependency,
                     db: Session = Depends(get_db)):
    form = await LoginForm.from_formdata(request)

    if await form.validate_on_submit():
        user = db.query(models.User).filter(
            models.User.email == form.email.data).first()
        if user and verify_passwd(form.password.data.encode('utf-8'),
                                  user.password):
            # Process login
            await login_user(response, user,
                                          remember=form.remember.data)
            print("User logged in successfully, redirecting to home...")
            # Redirect to the home page after successful login
            # return {"detail": "login success"}
            return RedirectResponse(url="/", status_code=303)
            # return JSONResponse(content={"redirect_to": "/"})

        return RedirectResponse(url="/login", status_code=303)
    else:
        return RedirectResponse(url="/login", status_code=303)


@portal.get("/test-cookie")
async def test_cookie(response: Response):
    class User:
        def __init__(self, data):
            self.__dict__.update(data)

    user_data = {"id": "1", "username": "odun",
                 "email": "hordunlarmy@gmail.com"}

    user = User(user_data)
    rem = False
    token_data = await login_user(response, user,
                                  remember=rem)
    return {"message": "Test cookie set"}


@portal.get("/logout")
async def logout(response: Response):
    await logout_user(response)
    return {"detail": "logout success"}
    return RedirectResponse(url="/", status_code=303)


@portal.get('/profile', response_class=HTMLResponse)
async def profile(request: Request, user: user_dependency,
                  db: Session = Depends(get_db)):
    form = UpdateProfileForm()
    form.username = user.username
    form.email = user.email
    return templates.TemplateResponse('profile.html', {"request": request,
                                                       "form": form,
                                                       "title": "Profile",
                                                       "current_user": user})


@portal.post('/profile', response_class=HTMLResponse)
async def profile_post(request: Request, user: user_dependency,
                       db: Session = Depends(get_db)):
    form = UpdateProfileForm(await request.form())
    if form.validate():
        current_user.username = form.username
        current_user.email = form.email
        db.commit()
        # FastAPI doesn't support Flask's flash; use alternative
        # like session cookies or frontend handling
        return RedirectResponse(url='/profile')


@portal.get('/history', response_class=HTMLResponse)
async def history(request: Request,
                  user: Annotated[TokenData, Depends(current_user)],
                  db: Session = Depends(get_db)):
    if user is None:
        return RedirectResponse(url="/login")
    else:
        messages = db.query(models.Message).filter_by(
            user_id=current_user.id).all()
        user_messages = {}
        for message in messages:
            decrypted_key = decrypt_key(message.key)
            decrypted_message = decrypt_message(
                message.message, decrypted_key, message.iv)
            user_messages[message.id] = decrypted_message
        return templates.TemplateResponse('history.html',
                                          {"request": request,
                                           "messages": user_messages,
                                           "title": "History",
                                           "current_user": user})


@portal.get('/delete', response_class=HTMLResponse)
async def delete_message(request: Request, user: user_dependency,
                         db: Session = Depends(get_db)):
    return {"detail": "Deleted"}
