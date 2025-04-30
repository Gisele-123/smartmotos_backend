from flask import Blueprint, request, jsonify
from models import Booking, Passenger, Driver
from extensions import db
import datetime
from functools import wraps
import jwt
from config import Config
from flutterwave import initialize_payment
import uuid


booking_bp = Blueprint('booking', __name__)

PRICING = {
    'base_fare': 500,
    'per_km': 10,
    'per_minute': 1
}

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

@booking_bp.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    data = request.get_json()
    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')
    pickup_time = datetime.datetime.strptime(data.get('pickup_time'), "%Y-%m-%dT%H:%M:%S")
    payment_method = data.get('payment_method')
    waypoints = data.get('waypoints', [])
    driver_id = data.get('driver_id')

    driver = Driver.query.filter_by(id=driver_id, status='available').first()
    if not driver:
        return jsonify({'message': 'The selected driver is not available'}), 400

    fare = PRICING['base_fare']

    tx_ref = str(uuid.uuid4())
    redirect_url = "https://yourdomain.com/payment/callback" # don't have frontend url so far

    payment_response = initialize_payment(fare, current_user.email, tx_ref, redirect_url)

    if payment_response["status"] != "success":
        return jsonify({"message": "Payment initialization failed"}), 400

    booking = Booking(
        passenger_id=current_user.id,
        driver_id=driver.id,
        pickup_location=pickup_location,
        dropoff_location=dropoff_location,
        pickup_time=pickup_time,
        payment_method=payment_method,
        status='pending',
        fare=fare,
        payment_status='pending'
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        'message': 'Booking created successfully. Proceed to payment.',
        'payment_link': payment_response["data"]["link"],
        'booking_id': booking.id
    }), 201

@booking_bp.route('/api/payment/callback', methods=['GET'])
def payment_callback():
    status = request.args.get('status')
    tx_ref = request.args.get('tx_ref')
    transaction_id = request.args.get('transaction_id')

    if status == 'successful':
        booking = Booking.query.filter_by(payment_status='pending').filter(Booking.status != 'cancelled').first()
        if booking:
            booking.payment_status = 'paid'
            db.session.commit()
            return jsonify({'message': 'Payment verified and updated'}), 200

    return jsonify({'message': 'Payment failed or cancelled'}), 400

@booking_bp.route('/api/bookings', methods=['GET'])
@token_required
def get_bookings(current_user):
    bookings = Booking.query.filter_by(passenger_id=current_user.id).all()
    return jsonify([{
        'id': b.id,
        'pickup_location': b.pickup_location,
        'dropoff_location': b.dropoff_location,
        'pickup_time': b.pickup_time.isoformat(),
        'payment_method': b.payment_method,
        'status': b.status,
        'fare': b.fare,
        'payment_status': b.payment_status
    } for b in bookings]), 200

@booking_bp.route('/api/bookings/<int:booking_id>', methods=['GET'])
@token_required
def get_booking_by_id(current_user, booking_id):
    booking = Booking.query.filter_by(id=booking_id, passenger_id=current_user.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    return jsonify({
        'id': booking.id,
        'pickup_location': booking.pickup_location,
        'dropoff_location': booking.dropoff_location,
        'pickup_time': booking.pickup_time.isoformat(),
        'payment_method': booking.payment_method,
        'status': booking.status,
        'fare': booking.fare,
        'payment_status': booking.payment_status
    }), 200

@booking_bp.route('/api/bookings/<int:booking_id>', methods=['PUT'])
@token_required
def update_booking(current_user, booking_id):
    booking = Booking.query.filter_by(id=booking_id, passenger_id=current_user.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    data = request.get_json()
    booking.pickup_location = data.get('pickup_location', booking.pickup_location)
    booking.dropoff_location = data.get('dropoff_location', booking.dropoff_location)
    booking.payment_method = data.get('payment_method', booking.payment_method)
    db.session.commit()

    return jsonify({'message': 'Booking updated successfully'}), 200

@booking_bp.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@token_required
def cancel_booking(current_user, booking_id):
    booking = Booking.query.filter_by(id=booking_id, passenger_id=current_user.id).first()
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    booking.status = 'cancelled'
    db.session.commit()

    return jsonify({'message': 'Booking cancelled successfully'}), 200
