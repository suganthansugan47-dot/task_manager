import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # In a real deployment, set this via an environment variable and keep it secret.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'taskmanager.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # How long a login token stays valid, in hours.
    JWT_EXP_HOURS = 24
