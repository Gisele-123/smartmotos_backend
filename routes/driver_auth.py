from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import Driver
from extensions import db, get_twilio_client, get_twilio_service_verify_sid
import jwt
from datetime import datetime, timedelta
from config import Config
from functools import wraps
from datetime import datetime
import re

driver_auth_bp = Blueprint('driver_auth', __name__, url_prefix='/api/driver')

def validate_rwanda_phone(phone):
    """Validate Rwanda phone number format"""
    return re.match(r'^\+250\d{9}$', phone)

def validate_license_number(license):
    """Basic license number validation"""
    return re.match(r'^[A-Z]{2}\d{5,10}$', license)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_driver = Driver.query.get(data['id'])
            if not current_driver:
                return jsonify({'error': 'Invalid token - driver not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401

        return f(current_driver, *args, **kwargs)
    return decorated

@driver_auth_bp.route('/onboarding', methods=['POST'])
def driver_onboarding():
    # Initialize response data
    response = {
        'success': False,
        'message': '',
        'driver_id': None,
        'verification_status': None
    }

    try:
        # 1. Validate JSON data
        if not request.is_json:
            response['message'] = 'Request must be JSON'
            return jsonify(response), 400

        data = request.get_json()

        # 2. Validate required fields
        required_fields = {
            'phone': {'type': str, 'validator': validate_rwanda_phone},
            'service_provider': {'type': str, 'options': ['MTN', 'Airtel']},
            'vehicle_type': {'type': str, 'options': ['bike', 'car']},
            'license_number': {'type': str, 'validator': validate_license_number},
            'password': {'type': str, 'min_length': 6},
            'confirm_password': {'type': str}
        }

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            response['message'] = f'Missing required fields: {", ".join(missing_fields)}'
            return jsonify(response), 400

        # 3. Field-specific validation
        errors = []
        
        # Phone validation
        if not isinstance(data['phone'], str) or not validate_rwanda_phone(data['phone']):
            errors.append('Phone must be a valid Uganda number (+256XXXXXXXXX)')
        
        # Password validation
        if len(data['password']) < 6:
            errors.append('Password must be at least 6 characters')
        if data['password'] != data['confirm_password']:
            errors.append('Passwords do not match')
        
        # Service provider validation
        if data['service_provider'] not in required_fields['service_provider']['options']:
            errors.append('Invalid service provider (must be MTN or Airtel)')
        
        # Vehicle type validation
        if data['vehicle_type'] not in required_fields['vehicle_type']['options']:
            errors.append('Invalid vehicle type (must be bike or car)')
        
        # License validation
        if not validate_license_number(data['license_number']):
            errors.append('License number must be in format AB123456')
        
        if errors:
            response['message'] = '; '.join(errors)
            return jsonify(response), 400

        # 4. Check for existing records
        if Driver.query.filter_by(phone=data['phone']).first():
            response['message'] = 'Phone number already registered'
            return jsonify(response), 409

        if Driver.query.filter_by(license_number=data['license_number']).first():
            response['message'] = 'License number already registered'
            return jsonify(response), 409

        # 5. Create driver record
        hashed_password = generate_password_hash(data['password'])
        
        new_driver = Driver(
            phone=data['phone'],
            password=hashed_password,
            service_provider=data['service_provider'],
            vehicle_type=data['vehicle_type'],
            license_number=data['license_number'],
            status='pending_verification'
        )

        db.session.add(new_driver)
        db.session.commit()

        # 6. Send verification SMS
        try:
            client = get_twilio_client(current_app)
            verify_sid = get_twilio_service_verify_sid(current_app)
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=data['phone'], channel='sms')

            # 7. Successful response
            response.update({
                'success': True,
                'message': 'Driver onboarding successful',
                'driver_id': new_driver.id,
                'verification_status': verification.status
            })
            return jsonify(response), 201

        except Exception as twilio_error:
            db.session.rollback()
            current_app.logger.error(f'Twilio error: {str(twilio_error)}')
            response['message'] = 'Failed to send verification SMS'
            return jsonify(response), 503

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Onboarding error: {str(e)}')
        response['message'] = 'Internal server error'
        return jsonify(response), 500

@driver_auth_bp.route('/verify/phone', methods=['POST'])
def driver_verify_phone():
    data = request.get_json()
    
    if not all(k in data for k in ['phone', 'code']):
        return jsonify({'error': 'Phone and code required'}), 400

    driver = Driver.query.filter_by(phone=data['phone']).first()
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    try:
        client = get_twilio_client(current_app)
        verify_sid = get_twilio_service_verify_sid(current_app)
        verification = client.verify.v2.services(verify_sid) \
            .verification_checks \
            .create(to=data['phone'], code=data['code'])

        if verification.status == 'approved':
            driver.status = 'available'
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Phone verified successfully'
            }), 200
        else:
            return jsonify({'error': 'Invalid verification code'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@driver_auth_bp.route('/login', methods=['POST'])
def driver_login():
    data = request.get_json()
    
    if not all(k in data for k in ['phone', 'password']):
        return jsonify({'error': 'Phone and password required'}), 400

    driver = Driver.query.filter_by(phone=data['phone']).first()
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    if driver.status != 'available':
        return jsonify({'error': 'Account not verified or disabled'}), 403

    if not check_password_hash(driver.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode(
        {
            'id': driver.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        },
        Config.SECRET_KEY,
        algorithm='HS256'
    )

    return jsonify({
        'success': True,
        'token': token,
        'driver': {
            'id': driver.id,
            'phone': driver.phone,
            'vehicle_type': driver.vehicle_type,
            'status': driver.status
        }
    }), 200

@driver_auth_bp.route('/profile', methods=['GET'])
@token_required
def driver_profile(current_driver):
    return jsonify({
        'id': current_driver.id,
        'phone': current_driver.phone,
        'vehicle_type': current_driver.vehicle_type,
        'service_provider': current_driver.service_provider,
        'license_number': current_driver.license_number,
        'status': current_driver.status
    }), 200
