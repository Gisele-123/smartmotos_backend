from flask import Blueprint, request, jsonify
from models import Booking, Driver
from extensions import db
from functools import wraps
import jwt
from config import Config

driver_bookings_bp = Blueprint('driver_bookings', __name__)

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

@driver_bookings_bp.route('/api/driver/accept-booking/<int:booking_id>', methods=['PUT'])
@driver_token_required
def accept_booking(current_driver, booking_id):
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.status != 'pending':
        return jsonify({'message': 'Booking is not available to accept'}), 400

    booking.driver_id = current_driver.id
    booking.status = 'accepted'
    db.session.commit()

    return jsonify({'message': 'Booking accepted successfully'}), 200

@driver_bookings_bp.route('/api/driver/my-bookings', methods=['GET'])
@driver_token_required
def my_bookings(current_driver):
    bookings = Booking.query.filter_by(driver_id=current_driver.id).all()

    result = []
    for booking in bookings:
        result.append({
            'id': booking.id,
            'pickup_location': booking.pickup_location,
            'dropoff_location': booking.dropoff_location,
            'status': booking.status
        })

    return jsonify(result), 200

@driver_bookings_bp.route('/api/driver/complete-booking/<int:booking_id>', methods=['PUT'])
@driver_token_required
def complete_booking(current_driver, booking_id):
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.driver_id != current_driver.id:
        return jsonify({'message': 'You are not assigned to this booking'}), 403

    if booking.status != 'accepted':
        return jsonify({'message': 'Booking cannot be completed'}), 400

    booking.status = 'completed'
    db.session.commit()

    return jsonify({'message': 'Booking completed successfully'}), 200
