from datetime import timedelta
from datetime import datetime
from functools import wraps
from dataclasses import dataclass

from werkzeug.local import LocalProxy
from flask import current_app
from flask import g
from flask import has_request_context
from flask import request
from flask import session
from flask import Response

import json

current_user = LocalProxy(lambda: _get_user())


def _get_user():
    if has_request_context():
        if "_login_user" not in g:
            current_app.login_manager._load_user()

        return g._login_user

    return None


def login_user(email: str, password: str, remember: bool = True):
    current_login_manager = current_app.login_manager
    IdPClient = current_login_manager.IdPClient
    tokens = IdPClient.login(email=email, 
                             passwd=password, 
                             agent=request.headers.get("User-Agent"))
    access_token = tokens.access
    refresh_token = tokens.refresh
    set_auth_cookies(access_token, refresh_token if remember else "")
    current_app.login_manager._load_user()

def logout_user():
    """
    Logs a user out. (You do not need to pass the actual user.).
    """
    remove_auth_cookies() # TODO blacklist

    #user_logged_out.send(current_app._get_current_object(), user=user) # not now

    current_app.login_manager._update_request_context_with_user()
    return True


def confirm_login(): # TODO
    """
    This sets the current session as fresh.
    """
    session["_fresh"] = True
    session["_id"] = current_app.login_manager._session_identifier_generator()


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view


def fresh_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        elif not current_user.is_fresh:
            return current_app.login_manager.needs_refresh()
        try:
            # current_app.ensure_sync available in Flask >= 2.0
            return current_app.ensure_sync(func)(*args, **kwargs)
        except AttributeError:  # pragma: no cover
            return func(*args, **kwargs)

    return decorated_view

def set_auth_cookies(access_token: str, refresh_token: str) -> None:
    IdPClient = current_app.login_manager.IdPClient
    set_cookie(Cookie(key=IdPClient.accessCookieName, 
                            value=access_token, 
                            httponly=True, 
                            secure=True, 
                            samesite="Lax", 
                            #max_age=tokens.access_exp_seconds, 
                            path="/"))
    set_cookie(Cookie(key=IdPClient.refreshCookieName, 
                            value=refresh_token, 
                            httponly=True, 
                            secure=True, 
                            samesite="Strict", 
                            #max_age=tokens.refresh_exp_seconds, 
                            path="/"))

def remove_auth_cookies():
    IdPClient = current_app.login_manager.IdPClient
    delete_cookie(Cookie(key=IdPClient.accessCookieName))
    delete_cookie(Cookie(key=IdPClient.refreshCookieName))

def _user_context_processor():
    return dict(current_user=_get_user())

# ===| Cookie Handler |===
@dataclass
class Cookie:
    key: str
    value: str = ""
    max_age: timedelta | int | None = None
    expires: str | datetime | int | float | None = None
    path: str | None = "/"
    domain: str | None = None
    secure: bool = False
    httponly: bool = False
    samesite: str | None = None
    partitioned: bool = False

def set_cookie(cookie: Cookie) -> None:
    if has_request_context():
        if "_cookies" not in g:
            g._cookies = {}
        g._cookies[json.dumps(cookie.__dict__)] = "set"

def delete_cookie(cookie: Cookie) -> None:
    if has_request_context():
        if "_cookies" not in g:
            g._cookies = {}
        g._cookies[json.dumps(cookie.__dict__)] = "delete"

def _cookieSeter(response: Response) -> Response:
    if has_request_context():
        if "_cookies" not in g:
            return response
        for cookie, action in g._cookies.items():
            if action == "set":
                response.set_cookie(**json.loads(f"{cookie}"))
            elif action == "delete":
                response.delete_cookie(json.loads(f"{cookie}")["key"])
    return response
