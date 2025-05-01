from flask import Blueprint, request, jsonify, current_app
from models import Driver
from extensions import db, get_twilio_client, get_twilio_service_verify_sid
import jwt
from datetime import datetime, timedelta
from config import Config
driver_auth_bp = Blueprint('driver_auth', __name__)

@driver_auth_bp.route('/api/driver/signup', methods=['POST'])
def driver_signup():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([phone, password, confirm_password]):
        return jsonify({'message': 'All fields are required'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    if Driver.query.filter_by(phone=phone).first():
        return jsonify({'message': 'Phone number already registered'}), 400

    new_driver = Driver(
        phone=phone,
        password=password,
        status='not_available'  # default status
    )

    db.session.add(new_driver)
    db.session.commit()

    # Send verification code using Twilio
    client = get_twilio_client(current_app)
    verify_sid = get_twilio_service_verify_sid(current_app)
    client.verify.v2.services(verify_sid).verifications.create(to=phone, channel='sms')

    return jsonify({'message': 'Driver signup successful. Verification code sent to phone.'}), 201

@driver_auth_bp.route('/api/driver/verify/phone', methods=['POST'])
def driver_verify_phone():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')

    if not phone or not code:
        return jsonify({'message': 'Phone and verification code are required'}), 400

    driver = Driver.query.filter_by(phone=phone).first()

    if not driver:
        return jsonify({'message': 'Driver not found'}), 404

    client = get_twilio_client(current_app)
    verify_sid = get_twilio_service_verify_sid(current_app)

    verification_check = client.verify.v2.services(verify_sid).verification_checks.create(to=phone, code=code)

    if verification_check.status == 'approved':
        driver.status = 'available'  # Once verified, activate driver
        db.session.commit()
        return jsonify({'message': 'Driver phone number verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification code'}), 400

@driver_auth_bp.route('/api/driver/login', methods=['POST'])
def driver_login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')

    if not phone or not password:
        return jsonify({'message': 'Phone number and password are required'}), 400

    driver = Driver.query.filter_by(phone=phone).first()

    if not driver:
        return jsonify({'message': 'Driver not found'}), 404

    if driver.status != 'available':
        return jsonify({'message': 'Driver account not available/verified'}), 403

    if driver.password != password:
        return jsonify({'message': 'Incorrect password'}), 401

    token = jwt.encode(
        {'id': driver.id, 'exp': datetime.utcnow() + timedelta(hours=1)},
        Config.SECRET_KEY,
        algorithm='HS256'
    )

    return jsonify({'token': token}), 200
