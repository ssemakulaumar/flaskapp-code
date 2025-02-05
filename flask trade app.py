from flask import Flask, request, jsonify, render_template
import requests
import hmac
import hashlib
import time
import logging
import base64
import json
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from urllib.parse import urlencode
import numpy as np
import pandas as pd

app = Flask(__name__)

# Binance API Configuration
BINANCE_API_KEY = "hoUL9VOrAORK2GN5sDejUl7j6hOTBcXAZaIr0f1njCLPs4TZPHS6KCTL6PQZbpi9"  # Replace with your Binance API key
BINANCE_SECRET_KEY = "5JSm571NyCDeCaURZQOz0C7dT5JPFg6eB7sKnHFMzsGcZhCTq07JVyYxhfnR8t22"  # Replace with your Binance secret key
BINANCE_BASE_URL = "wss://fsteam.binance.com"

# Email Notification Configuration
EMAIL_HOST = "smtp.gmail.com"  # Replace with your SMTP server
EMAIL_PORT = 587  # Replace with your SMTP server port
EMAIL_USER = "umardinaderson@gmail.com"  # Replace with your email
EMAIL_PASS = "cristalline0202"  # Replace with your email password
EMAIL_RECEIVER = "umardinaderson@gmail.com"  # Replace with the recipient's email

# Configure logging
logging.basicConfig(
    filename="trade_decisions.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# AI Trading Strategy Parameters
TRADING_STRATEGY = {
    "trade_quantity": 0.01,  # Adjust based on your preference
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30
}

def send_email_notification(subject, message):
    """Send an email notification."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def binance_request(endpoint, method='GET', params=None, signed=False):
    """Helper function to make signed or unsigned Binance API requests."""
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    
    if params is None:
        params = {}
    
    if signed:
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
    
    url = f"{BINANCE_BASE_URL}{endpoint}?{urlencode(params)}"
    response = requests.request(method, url, headers=headers)
    return response.json()

def fetch_market_price(symbol):
    """Fetch the current market price from Binance."""
    endpoint = "/api/v3/ticker/price"
    params = {"symbol": symbol}
    response = binance_request(endpoint, params=params)
    return float(response.get("price", 0))

def fetch_account_balance():
    """Fetch account balance from Binance."""
    endpoint = "/api/v3/account"
    response = binance_request(endpoint, signed=True)
    return response

def ai_trade_decision(symbol):
    """Make trade decision based on AI strategy."""
    prices = [fetch_market_price(symbol) for _ in range(TRADING_STRATEGY['rsi_period'] + 1)]
    rsi = "calculate_rsi"(prices, TRADING_STRATEGY['rsi_period'])
    
    if rsi is not None:
        if rsi < TRADING_STRATEGY['rsi_oversold']:
            return "BUY"
        elif rsi > TRADING_STRATEGY['rsi_overbought']:
            return "SELL"
    
    return None

def place_trade(symbol, side, quantity):
    """Place a market trade on Binance."""
    endpoint = "/api/v3/order"
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity
    }
    response = binance_request(endpoint, method='POST', params=params, signed=True)
    return response

@app.route('/api/trade', methods=['POST'])
def trade():
    """Endpoint to execute an AI-driven trade."""
    data = request.get_json()
    
    if "symbol" not in data:
        return jsonify({"error": "Missing required field: symbol"}), 400
    
    symbol = data["symbol"].upper()
    action = ai_trade_decision(symbol)
    quantity = TRADING_STRATEGY["trade_quantity"]
    
    if action is None:
        return jsonify({"message": "No trade action taken based on AI analysis."}), 200
    
    try:
        response = place_trade(symbol, action, quantity)
        logging.info(f"AI Trade executed: {response}")
        send_email_notification("Trade Executed", f"Action: {action}\nSymbol: {symbol}\nQuantity: {quantity}\nResponse: {response}")
        return jsonify({"message": "Trade executed successfully", "response": response}), 200
    except Exception as e:
        logging.error(f"Trade execution failed: {str(e)}")
        send_email_notification("Trade Execution Failed", f"Error: {str(e)}")
        return jsonify({"error": "Trade execution failed", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
