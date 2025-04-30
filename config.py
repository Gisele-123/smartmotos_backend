import os
from dotenv import load_dotenv

load_dotenv() 

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID')
    APP_NAME = os.getenv('APP_NAME')
    FLW_SECRET_KEY = os.getenv('FLW_SECRET_KEY')
    FLW_PUBLIC_KEY = os.getenv('FLW_PUBLIC_KEY')
    FLW_ENCRYPTION_KEY = os.getenv('FLW_ENCRYPTION_KEY')