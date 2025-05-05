from flask import Blueprint, request, jsonify
from extensions import db
from models import Location
import math
from datetime import datetime

location_bp = Blueprint('location', __name__)

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers using Haversine formula
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

def estimate_duration(distance_km):
    """
    Estimate trip duration based on distance
    Using average bike speed of 30km/h in urban areas
    """
    average_speed = 30  # km/h
    return (distance_km / average_speed) * 60  # Convert to minutes

@location_bp.route('/locations/calculate', methods=['POST'])
def calculate_route():
    data = request.get_json()
    
    # Get coordinates from request
    pickup_lat = data.get('pickup_lat')
    pickup_lng = data.get('pickup_lng')
    dropoff_lat = data.get('dropoff_lat')
    dropoff_lng = data.get('dropoff_lng')
    
    # Validate coordinates
    if None in [pickup_lat, pickup_lng, dropoff_lat, dropoff_lng]:
        return jsonify({'error': 'All coordinates are required'}), 400
    
    try:
        # Calculate distance using Haversine
        distance_km = haversine(
            float(pickup_lat), 
            float(pickup_lng), 
            float(dropoff_lat), 
            float(dropoff_lng)
        )
        
        # Estimate duration
        duration_mins = estimate_duration(distance_km)
        
        # Calculate fare
        base_fare = 500  # UGX
        per_km = 30      # UGX per km
        per_minute = 1   # UGX per minute
        
        sub_total = base_fare + (distance_km * per_km) + (duration_mins * per_minute)
        app_fee = sub_total * 0.04  # 4%
        total_fare = sub_total + app_fee
        
        # Save to database
        location = Location(
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            distance_km=distance_km,
            duration_mins=duration_mins,
            sub_total=sub_total,
            created_at=datetime.utcnow()
        )
        
        db.session.add(location)
        db.session.commit()
        
        return jsonify({
            'distance_km': round(distance_km, 2),
            'duration_mins': round(duration_mins, 2),
            'sub_total': round(sub_total, 2),
            'app_fee': round(app_fee, 2),
            'total_fare': round(total_fare, 2),
            'location_id': location.id,
            'message': 'Fare calculated successfully'
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid coordinate values'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to calculate route: ' + str(e)}), 500