import os

appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
fatoora_data_dir = os.path.join(appdata_dir, 'FatooraApp')
if not os.path.exists(fatoora_data_dir):
    os.makedirs(fatoora_data_dir, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fatoora-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(fatoora_data_dir, 'fatoora.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
