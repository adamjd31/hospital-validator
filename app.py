from flask import Flask, render_template, request, jsonify
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Twilio client - using environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Initialize Twilio client if credentials are available
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/')
def index():
    return "Hospital Email Validator Platform - Welcome!"

@app.route('/webhook-forward', methods=['POST'])
def webhook_forward():
    try:
        data = request.get_json()
        # Process webhook data here
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# For Vercel serverless deployment
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run(debug=True)
