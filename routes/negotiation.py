from flask import Blueprint, request, jsonify
from models import Negotiation, Booking
from extensions import db
from datetime import datetime

negotiation_bp = Blueprint('negotiation', __name__)

@negotiation_bp.route('/negotiations', methods=['POST'])
def create_negotiation():
    data = request.get_json()
    booking_id = data.get('booking_id')
    offer_amount = data.get('offer_amount')
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404
    
    negotiation = Negotiation(
        booking_id=booking_id,
        offer_amount=offer_amount,
        status='pending',
        created_at=datetime.utcnow()
    )
    
    db.session.add(negotiation)
    booking.status = 'bargaining'
    db.session.commit()
    
    # Notify the other party
    notify_parties(booking_id)
    
    return jsonify({
        'message': 'Negotiation started',
        'negotiation_id': negotiation.id
    }), 201

@negotiation_bp.route('/negotiations/<int:negotiation_id>/respond', methods=['POST'])
def respond_to_negotiation(negotiation_id):
    data = request.get_json()
    accepted = data.get('accepted')
    counter_offer = data.get('counter_offer')
    
    negotiation = Negotiation.query.get(negotiation_id)
    if not negotiation:
        return jsonify({'message': 'Negotiation not found'}), 404
    
    booking = Booking.query.get(negotiation.booking_id)
    
    if accepted:
        negotiation.status = 'accepted'
        booking.status = 'accepted'
        booking.sub_total = negotiation.offer_amount
        booking.app_fee = negotiation.offer_amount * 0.04
    elif counter_offer:
        # Create new negotiation entry for counter offer
        new_negotiation = Negotiation(
            booking_id=negotiation.booking_id,
            offer_amount=counter_offer,
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(new_negotiation)
    else:
        negotiation.status = 'rejected'
        booking.status = 'rejected'
    
    db.session.commit()
    notify_parties(negotiation.booking_id)
    
    return jsonify({
        'message': 'Negotiation updated',
        'status': negotiation.status
    }), 200

def notify_parties(booking_id):
    # Implement notification logic
    pass