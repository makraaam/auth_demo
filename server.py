import base64
import hashlib
import hmac
import json
from typing import Optional

from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response

app = FastAPI()

SECRET_KEY = "a225b459fcac3910ee15b0a1492a77f664289db9a98560ee151bf413e95270da"
PASSWORD_SALT = "b4522e07d98e6948b27b68ce45726f0638d750078126dcef0f702ee20235b645"


def sign_data(data: str) -> str:
    """Возвращает подписанные данные data"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    hash_password = hashlib.sha256((password + PASSWORD_SALT).encode()) \
        .hexdigest().lower()
    stored_password = users[username]["password"].lower()
    return hash_password == stored_password


users = {
    "vlada@mail.ru": {
        "name": "Vladislava",
        "password": "1ee25dff333c1c5afa9a296587b7d74f6340c58a18fe2068ce0128b3d1e7354e",
        "balance": 12222
    },
    "makram@mail.ru": {
        "name": "Makram",
        "password": "4945c213e1e685cdbaf9a41278447f1f1aa29aea400d14674f2823bd99226f10",
        "balance": "infinity"
    },
 }


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open("templates/login_page.html", "r") as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="txt/html")
        response.delete_cookie(key="username")
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}!<br />"
        f"Твой баланс: {users[valid_username]['balance']}",
        media_type="text/html")


@app.post("/login")
def process_login_page(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Ты кто? Я тебя не знаю!"
            }),
            media_type="application/json")

    response = Response(
        json.dumps({
            "success": True,
            "message": f"Привет, {user['name']}!<br /> Твой баланс: {user['balance']}"
        }),
        media_type="application/json")
    username_signed = base64.b64encode(username.encode()).decode() + "." + \
                      sign_data(username)

    response.set_cookie(key="username", value=username_signed)
    return response
