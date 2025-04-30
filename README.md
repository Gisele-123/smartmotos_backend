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

### Render deployment:
https://smartmotos-backend.onrender.com

### Passenger Endpoints:
POST /api/signup: Create a new passenger.

POST /api/login: Login a passenger and get a JWT token.

GET /api/bookings: View all bookings made by the passenger.

POST /api/bookings: Create a new booking (Triggers payment process).

GET /api/bookings/{booking_id}: Get a specific booking details by its booking_id.

DELETE /api/bookings/{booking_id}: Cancel a booking.

### Driver Endpoints:
POST /api/driver/signup: Create a new driver.

POST /api/driver/login: Login a driver and get a JWT token.

PUT /api/driver/status: Set driver status (e.g., available or unavailable).

PUT /api/driver/accept-booking/{booking_id}: Accept a booking.

PUT /api/driver/complete-booking/{booking_id}: Complete a booking.

GET /api/driver/my-bookings: View all bookings assigned to the driver.

### Flow for Payment & Redirect
1. The backend provides a payment_link for the frontend after booking creation (API /api/bookings POST).

2. The frontend must redirect the user to this payment_link to complete payment.

3. After payment, Flutterwave sends a callback to the backend (/api/payment/callback) to verify and update the booking status.

4. The backend updates the booking's payment status to 'paid' upon successful verification.

### Key Points to Test:
1. **Booking Creation**: Use `POST /api/bookings` to simulate booking and get the payment link.
2. **Payment Link**: Ensure the frontend redirects the user to the `payment_link` for payment.
3. **Callback Simulation**: You can manually trigger the callback for testing by calling `/api/payment/callback` with `status=successful`.
