from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import re
import random
import string
from extensions import db, get_twilio_client, get_twilio_service_verify_sid
from models import Passenger
from config import Config

auth_bp = Blueprint('auth', __name__)

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=5))

def validate_phone_number(phone_number):
    return re.match(r'^\+?[1-9]\d{1,14}$', phone_number) is not None

def send_custom_verification_sms(phone_number):
    client = get_twilio_client(current_app)
    verify_sid = get_twilio_service_verify_sid(current_app)
    try:
        verification = client.verify.v2.services(verify_sid).verifications.create(
            to=phone_number,
            channel="sms"
        )
        return verification.status
    except Exception as e:
        print("Twilio error:", e)
        return None

def send_phone_verification(phone_number):
    return send_custom_verification_sms(phone_number)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required_fields = ['name', 'email', 'phone', 'password', 'confirm_password']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing fields'}), 400

    if not validate_phone_number(data['phone']):
        return jsonify({'message': 'Invalid phone format'}), 400

    if data['password'] != data['confirm_password']:
        return jsonify({'message': 'Passwords do not match'}), 400

    if Passenger.query.filter_by(email=data['email']).first() or Passenger.query.filter_by(phone=data['phone']).first():
        return jsonify({'message': 'Email or phone already registered'}), 400

    passenger = Passenger(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        password=generate_password_hash(data['password']),
        phone_verified=False
    )

    try:
        db.session.add(passenger)
        db.session.commit()
        if send_phone_verification(data['phone']):
            return jsonify({'message': 'Signup successful, verification sent'}), 201
        else:
            db.session.delete(passenger)
            db.session.commit()
            return jsonify({'message': 'Failed to send verification'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@auth_bp.route('/verify/phone', methods=['POST'])
def verify_phone():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')

    if not phone or not code:
        return jsonify({'error': 'Phone number and code are required'}), 400

    try:
        client = get_twilio_client(current_app)
        verification_check = client.verify.v2.services(current_app.config['TWILIO_VERIFY_SERVICE_SID']).verification_checks.create(
            to=phone,
            code=code
        )

        if verification_check.status == 'approved':
            passenger = Passenger.query.filter_by(phone=phone).first()
            if passenger:
                passenger.phone_verified = True
                db.session.commit()
            return jsonify({'message': 'Phone verified successfully!'}), 200
        else:
            return jsonify({'error': 'Invalid verification code'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def passenger_login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')

    if not phone or not password:
        return jsonify({'error': 'Phone and password are required'}), 400

    passenger = Passenger.query.filter_by(phone=phone).first()

    if not passenger:
        return jsonify({'error': 'Passenger not found'}), 404

    if not check_password_hash(passenger.password, password):
        return jsonify({'error': 'Incorrect password'}), 401

    token = jwt.encode({
        'id': passenger.id,
    }, Config.SECRET_KEY, algorithm='HS256')

    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'passenger': {
            'id': passenger.id,
            'name': passenger.name,
            'phone': passenger.phone
        }
    }), 200

@auth_bp.route('/password/forgot', methods=['POST'])
def forgot_password():
    data = request.get_json()
    phone = data.get('phone')

    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400

    passenger = Passenger.query.filter_by(phone=phone).first()

    if not passenger:
        return jsonify({'error': 'Passenger not found'}), 404

    if send_phone_verification(phone):
        return jsonify({'message': 'Verification code sent via SMS'}), 200
    else:
        return jsonify({'error': 'Failed to send verification code'}), 500

@auth_bp.route('/password/reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([phone, code, new_password, confirm_password]):
        return jsonify({'error': 'All fields are required'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    passenger = Passenger.query.filter_by(phone=phone).first()
    if not passenger:
        return jsonify({'error': 'Passenger not found'}), 404

    try:
        client = get_twilio_client(current_app)
        verification_check = client.verify.v2.services(current_app.config['TWILIO_VERIFY_SERVICE_SID']) \
            .verification_checks.create(to=phone, code=code)

        if verification_check.status == 'approved':
            passenger.password = generate_password_hash(new_password)
            db.session.commit()
            return jsonify({'message': 'Password reset successful'}), 200
        else:
            return jsonify({'error': 'Invalid verification code'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
