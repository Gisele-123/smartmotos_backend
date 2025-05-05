# SmartMotos Backend API

Complete ride-hailing solution for motorbikes with real-time demand tracking and payment integration.

## Base URL
`https://smartmotos-backend.onrender.com`

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Gisele-123/smartmotos_backend.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## Authentication
All endpoints (except public ones) require JWT in header:
`Authorization: Bearer <your_token>`

## Passenger Endpoints

### Account Management
- **POST /api/signup**  
  Create new passenger account  
  ```json
  {
    "name": "string",
    "email": "string",
    "phone": "string",
    "password": "string",
    "confirm_password": "string"
  }
  ```

- **POST /api/verify/phone**  
  Verify phone with SMS code  
  ```json
  {
    "phone": "string",
    "code": "string"
  }
  ```

- **POST /api/login**  
  Get JWT token  
  ```json
  {
    "phone": "string",
    "password": "string"
  }
  ```

### Location & Demand
- **PUT /api/passenger/update-location**  
  Update passenger coordinates  
  ```json
  {
    "latitude": float,
    "longitude": float
  }
  ```

- **PUT /api/passenger/need-bike**  
  Set bike demand status  
  ```json
  {
    "need_bike": boolean
  }
  ```

### Booking Management
- **POST /api/bookings**  
  Create new booking  
  ```json
  {
    "pickup_location": "string",
    "dropoff_location": "string",
    "pickup_time": "datetime",
    "payment_method": "string",
    "driver_id": integer
  }
  ```

- **GET /api/bookings**  
  List all passenger's bookings

- **GET /api/bookings/{id}**  
  Get booking details

- **PUT /api/bookings/{id}**  
  Update booking  
  ```json
  {
    "pickup_location": "string",
    "dropoff_location": "string",
    "payment_method": "string"
  }
  ```

- **DELETE /api/bookings/{id}**  
  Cancel booking

### Password Recovery
- **POST /api/password/forgot**  
  Initiate password reset  
  ```json
  {
    "phone": "string"
  }
  ```

- **POST /api/password/reset**  
  Complete password reset  
  ```json
  {
    "phone": "string",
    "code": "string",
    "new_password": "string",
    "confirm_password": "string"
  }
  ```

## Driver Endpoints

### Authentication
- **POST /api/driver/signup**  
  ```json
  {
    "phone": "string",
    "password": "string",
    "confirm_password": "string"
  }
  ```

- **POST /api/driver/login**  
  ```json
  {
    "phone": "string",
    "password": "string"
  }
  ```

### Operations
- **PUT /api/driver/status**  
  Set availability  
  ```json
  {
    "status": "available/unavailable"
  }
  ```

- **PUT /api/driver/update-location**  
  Update coordinates  
  ```json
  {
    "latitude": float,
    "longitude": float
  }
  ```

- **PUT /api/driver/accept-booking/{id}**  
  Accept booking request

- **PUT /api/driver/complete-booking/{id}**  
  Mark booking as complete

- **GET /api/driver/my-bookings**  
  List driver's active bookings

## Public APIs (No Auth Required)

### Demand Tracking
- **GET /api/passengers/needing-bikes**  
  Returns passengers actively needing bikes:
  ```json
  [
    {
      "id": integer,
      "name": "string",
      "phone": "string",
      "latitude": float,
      "longitude": float,
      "location_updated_at": "datetime"
    }
  ]
  ```

- **GET /api/passengers/nearby-demand**  
  Find passengers in radius (params: `lat`, `lng`, `radius`)

## Payment Flow
1. Booking creation → returns `payment_link`
2. User completes payment via Flutterwave
3. System verifies via `/api/payment/callback`
4. Booking status updates to "paid"

## Testing Guide

### Sample Data
**Passenger Signup**:
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+254712345679",
  "password": "secure123",
  "confirm_password": "secure123"
}
```

**Create Booking**:
```json
{
  "pickup_location": "Nairobi CBD",
  "dropoff_location": "Westlands",
  "pickup_time": "2023-12-15T14:30:00",
  "payment_method": "mpesa"
}
```

### Test Sequence
1. Passenger signup → verify phone → login
2. Update location → set need_bike status
3. Create booking → test payment flow
4. As driver: check nearby demand → accept booking

## Error Codes
| Code | Meaning               |
|------|-----------------------|
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 404  | Not Found             |
| 500  | Internal Server Error |
```
