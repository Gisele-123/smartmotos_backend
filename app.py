from flask import Flask
from config import Config
from extensions import db, init_twilio
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    init_twilio(app)

    from models import Passenger, Booking, Driver

    with app.app_context():
        # db.drop_all()
        db.create_all()

    # Import blueprints
    from routes.passenger_auth import auth_bp
    from routes.bookings import booking_bp
    from routes.driver_auth import driver_auth_bp
    from routes.driver_status import driver_status_bp
    from routes.driver_bookings import driver_bookings_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(driver_auth_bp)
    app.register_blueprint(driver_status_bp)
    app.register_blueprint(driver_bookings_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
