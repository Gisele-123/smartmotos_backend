from flask import Blueprint, request, jsonify
from models import Booking, Passenger, Driver, RouteDistance, Location
from extensions import db
import datetime
from functools import wraps
import jwt
from config import Config
from flutterwave import initialize_payment
import uuid
from enum import Enum
import math
import random

booking_bp = Blueprint('booking', __name__)

PRICING = {
    'base_fare': 500,  # UGX
    'per_km': 30,      # UGX per km
    'per_minute': 1    # UGX per minute
}

class BookingStatus(Enum):
    PENDING = 'pending'
    DRIVER_ASSIGNED = 'driver_assigned'
    ACCEPTED = 'accepted'
    BARGAINING = 'bargaining'
    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

def get_distance(pickup, dropoff):
    """
    Get distance between two locations using RouteDistance table
    Returns distance in km or None if not found
    """
    route = RouteDistance.query.filter(
        ((RouteDistance.start_location.ilike(pickup)) & 
         (RouteDistance.end_location.ilike(dropoff))) |
        ((RouteDistance.start_location.ilike(dropoff)) & 
         (RouteDistance.end_location.ilike(pickup)))
    ).first()
    
    return route.distance_km if route else None

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))  # Earth radius in km

def find_nearest_driver(pickup_lat, pickup_lng, max_distance_km=5):
    """Find nearest available driver within radius"""
    # Get all available drivers
    available_drivers = Driver.query.filter(Driver.status == 'available').all()
    
    if not available_drivers:
        return None
    
    closest_driver = None
    min_distance = float('inf')
    
    for driver in available_drivers:
        # Skip drivers without location data
        if driver.latitude is None or driver.longitude is None:
            continue
            
        distance = haversine(pickup_lat, pickup_lng, driver.latitude, driver.longitude)
        
        if distance < min_distance and distance <= max_distance_km:
            min_distance = distance
            closest_driver = driver
    
    return closest_driver


def notify_driver(driver_id, booking_id):
    """
    Simulate notifying driver about new booking
    Returns bool for success
    """
    driver = Driver.query.get(driver_id)
    if not driver:
        return False
    
    driver.last_notified = datetime.datetime.utcnow()
    driver.pending_booking_id = booking_id
    db.session.commit()
    
    print(f"Driver {driver_id} notified about booking {booking_id}")
    return True

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = Passenger.query.get(data['id'])
            if not current_user:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


@booking_bp.route('/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['pickup_location', 'dropoff_location']):
        return jsonify({'error': 'Missing location data'}), 400
    
    # Calculate distance
    try:
        pickup = data['pickup_location']
        dropoff = data['dropoff_location']
        
        if isinstance(pickup, dict) and isinstance(dropoff, dict):
            # Coordinate-based booking
            distance = haversine(
                float(pickup['lat']), float(pickup['lng']),
                float(dropoff['lat']), float(dropoff['lng'])
            )
            location_str = f"{pickup['lat']},{pickup['lng']} to {dropoff['lat']},{dropoff['lng']}"
        else:
            # Address-based booking
            return jsonify({'error': 'Address lookup requires implementation'}), 400
        
        # Calculate fare
        fare = PRICING['base_fare'] + (PRICING['per_km'] * distance)
        
        # Find driver
        driver = find_nearest_driver(
            float(pickup['lat']), 
            float(pickup['lng'])
        )
        
        if not driver:
            return jsonify({'error': 'No available drivers nearby'}), 404
        
        # Create booking
        booking = Booking(
            passenger_id=current_user.id,
            driver_id=driver.id,
            pickup_location=location_str,
            fare=fare,
            status=BookingStatus.PENDING.value,
            payment_method=data.get('payment_method', 'cash')
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'booking_id': booking.id,
            'driver_id': driver.id,
            'fare': fare,
            'status': booking.status
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid coordinate values'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
 
@booking_bp.route('/bookings/<int:booking_id>/accept', methods=['POST'])
@token_required
def accept_booking(current_user, booking_id):
    booking = Booking.query.get(booking_id)
    if not booking or booking.driver_id != current_user.id:
        return jsonify({'error': 'Booking not found or unauthorized'}), 404
    
    if booking.status not in [BookingStatus.PENDING.value, BookingStatus.BARGAINING.value]:
        return jsonify({'error': 'Cannot accept booking in current state'}), 400
    
    booking.status = BookingStatus.ACCEPTED.value
    db.session.commit()
    
    # Process payment
    tx_ref = str(uuid.uuid4())
    total_amount = booking.fare * 1.04  # Add 4% fee
    
    payment_response = initialize_payment(
        amount=total_amount,
        email=current_user.email,
        tx_ref=tx_ref,
        redirect_url=f"{Config.BASE_URL}/payment/callback"
    )
    
    if payment_response.get("status") != "success":
        return jsonify({"error": "Payment initialization failed"}), 400
    
    booking.payment_reference = tx_ref
    db.session.commit()
    
    return jsonify({
        'success': True,
        'payment_link': payment_response["data"]["link"],
        'booking_status': booking.status
    })

@booking_bp.route('/bookings/<int:booking_id>/reject', methods=['POST'])
@token_required
def reject_booking(current_user, booking_id):
    booking = Booking.query.get(booking_id)
    if not booking or booking.driver_id != current_user.id:
        return jsonify({'error': 'Booking not found or unauthorized'}), 404
    
    if booking.status not in [BookingStatus.PENDING.value, BookingStatus.BARGAINING.value]:
        return jsonify({'error': 'Cannot reject booking in current state'}), 400
    
    booking.status = BookingStatus.REJECTED.value
    db.session.commit()
    
    return jsonify({'success': True})

@booking_bp.route('/bookings', methods=['GET'])
@token_required
def get_bookings(current_user):
    bookings = Booking.query.filter_by(passenger_id=current_user.id).all()
    return jsonify([{
        'id': b.id,
        'driver_id': b.driver_id,
        'pickup_location': b.pickup_location,
        'status': b.status,
        'fare': b.fare,
        'created_at': b.pickup_time.isoformat()
    } for b in bookings])

@booking_bp.route('/payment/callback', methods=['GET'])
def payment_callback():
    tx_ref = request.args.get('tx_ref')
    status = request.args.get('status')
    
    if status == 'successful':
        booking = Booking.query.filter_by(payment_reference=tx_ref).first()
        if booking:
            booking.payment_status = 'paid'
            booking.status = BookingStatus.ACCEPTED.value
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'error': 'Payment verification failed'}), 400