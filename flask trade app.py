from flask import Flask, request, jsonify
from flask import Flask, request, jsonify, render_template
import requests
import random  # For simulating market conditions (replace with real API calls)
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from matplot import pyplot as plt # type: ignore
import io
import base64
import json


app = Flask(__name__)

@app.route('/')
def home():
    """Serve the HTML dashboard."""
    return render_template('index.html')

@app.route('/api/visualize', methods=['GET'])
def visualize_trades():
    """
    Generate a line chart and return it as a Base64 image.
    """
    try:
        # Logic to create the chart goes here (e.g., matplotlib or another library)
        # Ensure it outputs a Base64-encoded PNG image.
        chart_base64 = "data:image/png;base64,..."

        return jsonify({"image": chart_base64}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Configure logging
logging.basicConfig(
    filename="trade_decisions.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Email notification configuration
EMAIL_HOST = "smtp.example.com"  # Replace with your SMTP server
EMAIL_PORT = 587  # Replace with your SMTP server port
EMAIL_USER = "umardinaderson@gmail.com"  # Replace with your email address
EMAIL_PASS = "cristalline0202"  # Replace with your email password
EMAIL_RECEIVER = "umardinaderson@gmail.com"  # Replace with the recipient's email address

# Exness API configuration
EXNESS_API_URL = "fapi.binance.com"  # Replace with the correct Exness API base URL
EXNESS_API_KEY = "732655e0d3090c971a2166144d9bb8eeee397d49087f26ba4342045a796c385d"  # Replace with your actual Exness API key

# Trading strategy parameters
TRADING_STRATEGY = {
    "short_moving_average_period": 5,  # Short moving average (e.g., 5 prices)
    "long_moving_average_period": 20,  # Long moving average (e.g., 20 prices)
    "rsi_threshold_buy": 30,  # RSI below this value indicates oversold (buy)
    "rsi_threshold_sell": 70,  # RSI above this value indicates overbought (sell)
    "trade_quantity": 1  # Fixed quantity for trades
}

# Simulated price history for visualization
price_history = [random.uniform(95, 105) for _ in range(50)]

@app.route('/')
def home():
    """Serve the HTML dashboard."""
    return render_template('index.html')

@app.route('/api/visualize', methods=['GET'])
def visualize_trades():
    """
    Generate a line chart and return it as a Base64 image.
    """
    try:
        # Generate timestamps for visualization
        timestamps = [datetime.now().strftime("%H:%M:%S") for _ in range(len(price_history))]
        
        # Generate the chart
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, price_history, label="Price History", color="blue")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.title("Market Trends")
        plt.legend()
        plt.xticks(rotation=45)
        
        # Save chart as Base64 image
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        encoded_image = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        
        return jsonify({"image": f"data:image/png;base64,{encoded_image}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

def fetch_market_price(asset):
    """
    Fetch the current market price for a given asset.
    Replace this with a real API call to fetch live market data.
    """
    try:
        price = random.uniform(95, 105)  # Example: Simulated price range
        price_history.append(price)
        if len(price_history) > 50:  # Keep history size manageable
            price_history.pop(0)
        return price
    except Exception as e:
        raise RuntimeError(f"Failed to fetch market price: {e}")

def calculate_moving_average(prices, period):
    """Calculate the moving average for the given period."""
    if len(prices) < period:
        return None  # Not enough data
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    """Calculate the Relative Strength Index (RSI)."""
    if len(prices) < period:
        return None  # Not enough data

    gains = []
    losses = []
    for i in range(1, period + 1):
        change = prices[-i] - prices[-i - 1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))

    average_gain = sum(gains) / period if gains else 0
    average_loss = sum(losses) / period if losses else 0

    if average_loss == 0:
        return 100  # RSI is 100 when there are no losses

    rs = average_gain / average_loss
    return 100 - (100 / (1 + rs))

def trading_logic(asset):
    """
    Evaluate trading logic based on the market price.
    Returns the decision: "BUY", "SELL", or None.
    """
    try:
        current_price = fetch_market_price(asset)
        short_ma = calculate_moving_average(price_history, TRADING_STRATEGY["short_moving_average_period"])
        long_ma = calculate_moving_average(price_history, TRADING_STRATEGY["long_moving_average_period"])
        rsi = calculate_rsi(price_history)

        logging.info(f"Price: {current_price}, Short MA: {short_ma}, Long MA: {long_ma}, RSI: {rsi}")

        if short_ma and long_ma and short_ma > long_ma:
            return "BUY", current_price, f"Short MA {short_ma} > Long MA {long_ma}"
        elif short_ma and long_ma and short_ma < long_ma:
            return "SELL", current_price, f"Short MA {short_ma} < Long MA {long_ma}"
        elif rsi and rsi < TRADING_STRATEGY["rsi_threshold_buy"]:
            return "BUY", current_price, f"RSI {rsi} < {TRADING_STRATEGY['rsi_threshold_buy']}"
        elif rsi and rsi > TRADING_STRATEGY["rsi_threshold_sell"]:
            return "SELL", current_price, f"RSI {rsi} > {TRADING_STRATEGY['rsi_threshold_sell']}"
        else:
            return None, current_price, "No conditions met"
    except Exception as e:
        raise RuntimeError(f"Trading logic failed: {e}")

@app.route('/api/trade/decision', methods=['POST'])
def make_trade_decision():
    """
    Endpoint to evaluate trading logic and make a trade decision.
    """
    data = request.get_json()

    if "asset" not in data:
        return jsonify({"error": "Missing required field: asset"}), 400

    asset = data["asset"]

    try:
        decision, price, reason = trading_logic(asset)
        logging.info(f"Decision: {decision}, Reason: {reason}")

        if decision:
            trade_payload = {
                "symbol": asset,
                "action": decision,
                "volume": TRADING_STRATEGY["trade_quantity"],
                "price": price,
                "type": "MARKET"
            }

            headers = {
                "Authorization": f"Bearer {EXNESS_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{EXNESS_API_URL}/trades", json=trade_payload, headers=headers)
            response_data = response.json()

            if response.status_code == 201:
                logging.info(f"Trade executed successfully. Action: {decision}, Asset: {asset}, Price: {price}, Reason: {reason}, Response: {response_data}")
                send_email_notification(
                    "Trade Executed Successfully",
                    f"Action: {decision}\nAsset: {asset}\nPrice: {price}\nReason: {reason}\nResponse: {response_data}"
                )
                return jsonify({
                    "message": f"Trade executed successfully. Action: {decision}",
                    "trade": response_data,
                    "reason": reason
                }), 201
            else:
                logging.warning(f"Trade execution failed. Action: {decision}, Asset: {asset}, Price: {price}, Reason: {reason}, Error: {response_data}")
                send_email_notification(
                    "Trade Execution Failed",
                    f"Action: {decision}\nAsset: {asset}\nPrice: {price}\nReason: {reason}\nError: {response_data}"
                )
                return jsonify({
                    "error": "Failed to execute trade.",
                    "details": response_data
                }), response.status_code

        else:
            return jsonify({
                "message": "No trading action taken.",
                "current_price": price,
                "reason": reason
            }), 200

    except Exception as e:
        logging.error(f"Error making trade decision: {e}")
        send_email_notification(
            "Trade Decision Error",
            f"An error occurred while making a trade decision: {e}"
        )
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/visualize', methods=['GET'])
def visualize_trades():
    """
    Endpoint to visualize trade performance and market trends.
    Generates a line chart of asset prices and overlays executed trades.
    """
    try:
        asset = request.args.get("asset", "Simulated Asset")
        timestamps = [datetime.now().strftime("%H:%M:%S") for _ in range(len(price_history))]
        trades = [random.choice(["BUY", "SELL", None]) for _ in range(len(price_history))]  # Replace with real trade history

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, price_history, label="Price History", color="blue")
        for i, trade in enumerate(trades):
            if trade == "BUY":
                plt.scatter(timestamps[i], price_history[i], color="green", label="Buy Signal" if i == 0 else "")
            elif trade == "SELL":
                plt.scatter(timestamps[i], price_history[i], color="red", label="Sell Signal" if i == 0 else "")

        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.title(f"Market Trends and Trades for {asset}")
        plt.legend()
        plt.xticks(rotation=45)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        encoded_image = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

        return jsonify({"image": f"data:image/png;base64,{encoded_image}"}), 200
    except Exception as e:
        logging.error(f"Visualization error: {e}")
        return jsonify({"error": "An error occurred while generating the visualization."}), 500

if __name__ == '__main__':
    app.run(debug=True)
