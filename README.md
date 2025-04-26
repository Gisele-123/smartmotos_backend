# SmartMotos App

This is a simple ride booking system where passengers can create bookings, and drivers can accept and complete them. The system also allows drivers to set their availability status, and passengers can cancel their bookings. This README covers the API endpoints, how to set up and run the application, and how to test using Postman.

## Setup

1. Clone the repository:
   git clone https://github.com/Gisele-123/smartmotos_backend.git

2. Install the required dependencies:
    pip install -r requirements.txt

3. Run your app:
    python app.py

## API Endpoints
### Passenger Endpoints:
POST /api/passenger/signup: Create a new passenger.

POST /api/passenger/login: Login a passenger and get a JWT token.

GET /api/bookings: View all bookings made by the passenger.

DELETE /api/bookings/<booking_id>: Cancel a booking.

### Driver Endpoints:
POST /api/driver/signup: Create a new driver.

POST /api/driver/login: Login a driver and get a JWT token.

PUT /api/driver/status: Set driver status (e.g., available or unavailable).

PUT /api/driver/accept-booking/<booking_id>: Accept a booking.

PUT /api/driver/complete-booking/<booking_id>: Complete a booking.

GET /api/driver/my-bookings: View all bookings assigned to the driver.