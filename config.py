import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fatoora-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'fatoora.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
