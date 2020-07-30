from functools import wraps
from flask import session, request, redirect, url_for,flash

def signin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/signin")
        return f(*args, **kwargs)
    return decorated_function
