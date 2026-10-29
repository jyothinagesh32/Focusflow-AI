import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret-key")
    # XAMPP MySQL default: user=root, no password, database=focusflow_ai.
    # If your MySQL root account has a password, set DATABASE_URL before running app.py.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:@127.0.0.1:3306/focusflow_ai"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
