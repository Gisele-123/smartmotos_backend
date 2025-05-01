from datetime import datetime
from extensions import db

class Passenger(db.Model):
    __tablename__ = 'registered_passengers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    verification_expiry = db.Column(db.DateTime)
    bookings = db.relationship('Booking', backref='passenger', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('registered_passengers.id'), nullable=False)
    pickup_location = db.Column(db.String(200), nullable=False)
    dropoff_location = db.Column(db.String(200), nullable=False)
    waypoints = db.Column(db.JSON)
    pickup_time = db.Column(db.Time, nullable=False)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    fare = db.Column(db.Float, nullable=False, default=0.0)  # Set default value for fare
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='not_active')

class DriverAvailability(db.Model):
    __tablename__ = 'driver_availabilities'
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

class Bike(db.Model):
    __tablename__ = 'bikes'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='available')
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    driver = db.relationship('Driver', backref=db.backref('bikes', lazy=True))

class RouteDistance(db.Model):
    __tablename__ = 'route_distances'

    id = db.Column(db.Integer, primary_key=True)
    start_location = db.Column(db.String(100), nullable=False)
    end_location = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)

    def as_tuple(self):
        return (self.start_location.lower(), self.end_location.lower())
    
