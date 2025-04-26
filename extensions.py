from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client

db = SQLAlchemy()

def init_twilio(app):
    app.twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

def get_twilio_client(app):
    return app.twilio_client

def get_twilio_service_verify_sid(app):
    return app.config['TWILIO_VERIFY_SERVICE_SID']
