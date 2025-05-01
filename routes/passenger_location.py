from flask import Blueprint, request, jsonify
from models import Passenger
from extensions import db
from functools import wraps
import jwt
from config import Config
from datetime import datetime, timedelta
import math

passenger_location_bp = Blueprint('passenger_location', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'message': 'Missing or invalid token'}), 401
        
        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = Passenger.query.get(data['id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@passenger_location_bp.route('/api/passenger/update-location', methods=['PUT'])
@token_required
def update_passenger_location(current_user):
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')

    if lat is None or lng is None:
        return jsonify({'message': 'Latitude and longitude required'}), 400

    current_user.latitude = lat
    current_user.longitude = lng
    current_user.location_updated_at = datetime.utcnow()
    
    db.session.commit()

    return jsonify({'message': 'Location updated successfully'}), 200

@passenger_location_bp.route('/api/passenger/need-bike', methods=['PUT'])
@token_required
def update_need_bike_status(current_user):
    data = request.get_json()
    need_bike = data.get('need_bike')

    if need_bike is None:
        return jsonify({'message': 'need_bike status is required'}), 400

    current_user.need_bike = bool(need_bike)
    db.session.commit()

    return jsonify({
        'message': 'Need bike status updated successfully',
        'need_bike': current_user.need_bike
    }), 200

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@passenger_location_bp.route('/api/passengers/nearby-demand', methods=['GET'])
def get_nearby_passengers_with_demand():
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    radius_km = float(request.args.get('radius', 2))  

    recent_threshold = datetime.utcnow() - timedelta(minutes=15)
    passengers = Passenger.query.filter(
        Passenger.need_bike == True,
        Passenger.location_updated_at >= recent_threshold,
        Passenger.latitude.isnot(None),
        Passenger.longitude.isnot(None)
    ).all()

    nearby_passengers = []
    for passenger in passengers:
        distance = haversine(lat, lng, passenger.latitude, passenger.longitude)
        if distance <= radius_km:
            nearby_passengers.append({
                'id': passenger.id,
                'name': passenger.name,
                'phone': passenger.phone,
                'latitude': passenger.latitude,
                'longitude': passenger.longitude,
                'distance_km': round(distance, 2),
                'location_updated_at': passenger.location_updated_at.isoformat()
            })

    return jsonify(nearby_passengers), 200

@passenger_location_bp.route('/api/passengers/needing-bikes', methods=['GET'])
def get_all_passengers_needing_bikes():
    recent_threshold = datetime.utcnow() - timedelta(minutes=15)
    passengers = Passenger.query.filter(
        Passenger.need_bike == True,
        Passenger.location_updated_at >= recent_threshold,
        Passenger.latitude.isnot(None),
        Passenger.longitude.isnot(None)
    ).all()

    result = [{
        'id': p.id,
        'name': p.name,
        'phone': p.phone,
        'latitude': p.latitude,
        'longitude': p.longitude,
        'location_updated_at': p.location_updated_at.isoformat()
    } for p in passengers]

    return jsonify(result), 200