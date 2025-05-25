from flask import Flask
import os
from config import Config
from extensions import db, init_twilio
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    init_twilio(app)
    migrate = Migrate(app, db)  

    from models import (
        Passenger, 
        Booking, 
        Driver,
        RouteDistance,
        Location,
        Negotiation
    )

    with app.app_context():
        # db.drop_all()  # Uncomment to reset database
        db.create_all()

    from routes.passenger_auth import auth_bp
    from routes.bookings import booking_bp
    from routes.driver_auth import driver_auth_bp
    from routes.driver_status import driver_status_bp
    from routes.driver_bookings import driver_bookings_bp
    from routes.passenger_location import passenger_location_bp
    from routes.location_service import location_bp 
    from routes.negotiation import negotiation_bp   
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(booking_bp, url_prefix='/api')
    app.register_blueprint(driver_auth_bp, url_prefix='/api/driver')
    app.register_blueprint(driver_status_bp, url_prefix='/api/driver')
    app.register_blueprint(driver_bookings_bp, url_prefix='/api/driver')
    app.register_blueprint(passenger_location_bp, url_prefix='/api/passenger')
    app.register_blueprint(location_bp, url_prefix='/api')
    app.register_blueprint(negotiation_bp, url_prefix='/api')  

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)