from flask import Blueprint, request, jsonify
from models import Driver
from extensions import db
from functools import wraps
import jwt
from config import Config

driver_status_bp = Blueprint('driver_status', __name__)

def driver_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'message': 'Missing or invalid token'}), 401
        
        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_driver = Driver.query.get(data['id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_driver, *args, **kwargs)
    return decorated

@driver_status_bp.route('/api/driver/status', methods=['PUT'])
@driver_token_required
def update_driver_status(current_driver):
    data = request.get_json()
    status = data.get('status')

    if status not in ['available', 'unavailable']:
        return jsonify({'message': 'Invalid status'}), 400

    current_driver.status = status
    db.session.commit()

    return jsonify({'message': 'Driver status updated successfully'}), 200
