import requests
from config import Config

def initialize_payment(amount, customer_email, tx_ref, redirect_url):
    url = "https://api.flutterwave.com/v3/payments"

    headers = {
        "Authorization": f"Bearer {Config.FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "RWF",
        "redirect_url": redirect_url,
        "payment_options": "card,mobilemoneyrwanda",
        "customer": {
            "email": customer_email,
        },
        "customizations": {
            "title": "Bike Booking Payment",
            "description": "Payment for bike ride booking"
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()
