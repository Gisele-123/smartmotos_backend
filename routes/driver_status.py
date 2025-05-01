from datetime import datetime
from flask import Blueprint, request, jsonify
from models import Driver
from extensions import db
from functools import wraps
import jwt
from config import Config
import math

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

@driver_status_bp.route('/api/driver/update-location', methods=['PUT'])
@driver_token_required
def update_driver_location(current_driver):
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')

    if lat is None or lng is None:
        return jsonify({'message': 'Latitude and longitude required'}), 400

    current_driver.latitude = lat
    current_driver.longitude = lng
    current_driver.location_updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': 'Location updated successfully'}), 200

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@driver_status_bp.route('/api/driver/nearby', methods=['GET'])
def get_nearby_drivers():
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    radius_km = float(request.args.get('radius', 2)) 

    all_drivers = Driver.query.filter_by(status='available').all()

    nearby = []
    for driver in all_drivers:
        if driver.latitude and driver.longitude:
            distance = haversine(lat, lng, driver.latitude, driver.longitude)
            if distance <= radius_km:
                nearby.append({
                'id': driver.id,
                'lat': driver.latitude,
                'lng': driver.longitude,
                'distance_km': round(distance, 2)
            })

    
    return jsonify(nearby), 200

