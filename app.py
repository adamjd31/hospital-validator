from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import pandas as pd
import phonenumbers
from validate_email import validate_email
import os
import uuid
import logging
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime
import json
from pyngrok import ngrok

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Twilio Configuration
TWILIO_ACCOUNT_SID = 'AC6b5ca71eb47231aaae71fd4cdadb2a47'  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = '09a6e00da1565eb12c53df5a1e4223cc'    # Replace with your Twilio Auth Token
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Updated to Twilio's WhatsApp sandbox number

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ZeroBounce configuration
ZEROBOUNCE_API_KEY = 'f6989f46b5034f839819c878a6901c43'

# Store messages in a JSON file
MESSAGES_FILE = 'messages.json'

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return {'messages': []}

def save_message(name, phone, old_email, new_email, status='Pending'):
    try:
        # Create messages file if it doesn't exist
        if not os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'w') as file:
                json.dump([], file)

        # Read existing messages
        with open(MESSAGES_FILE, 'r') as file:
            try:
                messages = json.load(file)
            except json.JSONDecodeError:
                messages = []

        # Add new message
        messages.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': name,
            'phone': phone,
            'old_email': old_email,
            'new_email': new_email,
            'status': status
        })

        # Save updated messages
        with open(MESSAGES_FILE, 'w') as file:
            json.dump(messages, file, indent=2)

        logger.info(f"Message saved successfully for {phone}")
        return True
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        return False

def send_whatsapp_notification(name, phone, invalid_email):
    try:
        # Format the phone number for WhatsApp
        whatsapp_to = f"whatsapp:+{phone}" if not phone.startswith('+') else f"whatsapp:{phone}"
        
        # Format the WhatsApp message
        message = f"""Dear {name},

We noticed your email address ({invalid_email}) in our records may be incorrect. Please reply with your correct email address to ensure you receive important updates from American Hospital Dubai.

Thank you,
American Hospital Dubai"""

        # Send WhatsApp message
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=whatsapp_to
        )
        logger.info(f"WhatsApp message sent successfully to {whatsapp_to}")
        return True, message.sid
        
    except Exception as e:
        logger.error(f"WhatsApp error: {str(e)}")
        return False, str(e)

def validate_email_address(email):
    if not email or pd.isna(email):
        return False, 'NOT VALID', 'Empty email address'
    
    try:
        # Basic format check
        if not '@' in email or not '.' in email:
            return False, 'NOT VALID', 'Invalid email format'
            
        # ZeroBounce API check
        url = f"https://api.zerobounce.net/v2/validate?api_key={ZEROBOUNCE_API_KEY}&email={email}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'valid':
            return True, 'VALID', 'Email is valid'
        elif data.get('did_you_mean'):
            return False, 'NOT VALID', f'Did you mean {data["did_you_mean"]}?'
        else:
            return False, 'NOT VALID', data.get('error', 'Invalid email')
            
    except Exception as e:
        logger.error(f"Error validating email {email}: {str(e)}")
        return False, 'NOT VALID', str(e)

def validate_phone_number(phone):
    if not phone or pd.isna(phone):
        return False, 'NOT VALID', 'Empty phone number'
        
    try:
        # Convert to string and remove any spaces or special characters
        phone = str(phone).strip().replace('+', '').replace(' ', '')
        
        # Check if it starts with 971 and has the correct length
        if not phone.startswith('971') or len(phone) != 12:
            return False, 'NOT VALID', 'Phone number must start with 971 and be 12 digits long'
            
        # Parse phone number with phonenumbers library (adding + for parsing)
        parsed_number = phonenumbers.parse('+' + phone)
        
        # Check if valid
        if phonenumbers.is_valid_number(parsed_number):
            return True, 'VALID', 'Phone number is valid'
        else:
            return False, 'NOT VALID', 'Invalid phone number format'
            
    except Exception as e:
        return False, 'NOT VALID', str(e)

def setup_ngrok():
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(3000)
        
        # Make the URL very visible in console
        webhook_url = f"{public_url}/whatsapp-webhook"
        print("\n" + "="*60)
        print("\nIMPORTANT - COPY THIS URL FOR TWILIO WEBHOOK:")
        print("\n" + webhook_url + "\n")
        print("Steps to set up:")
        print("1. Go to Twilio Console")
        print("2. Click Messaging → Try it out → Send a WhatsApp message")
        print("3. In 'WHEN A MESSAGE COMES IN', paste the URL above")
        print("\n" + "="*60 + "\n")
        
        return public_url
    except Exception as e:
        logger.error(f"Error setting up ngrok: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Only .xlsx files are allowed'}), 400
        
    try:
        # Generate unique filename
        unique_filename = f"{str(uuid.uuid4())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': unique_filename
        }), 200
        
    except Exception as e:
        logger.error(f'Error uploading file: {str(e)}')
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
def process_file():
    try:
        filename = request.json.get('filename')
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        # Read Excel file
        df = pd.read_excel(filepath, engine='openpyxl')
        
        # Replace NaN values with empty strings
        df = df.fillna('')
        
        # Validate required columns
        required_columns = ['Name', 'Email', 'Mobile Number']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400
        
        # Initialize new columns
        df['email_status'] = 'NOT CHECKED'
        df['email_message'] = ''
        df['phone_status'] = 'NOT CHECKED'
        df['phone_message'] = ''
        df['whatsapp_sent'] = 'NO'
        df['whatsapp_status'] = ''
        df['response_received'] = 'NO'
        
        # Process each row
        for idx, row in df.iterrows():
            # Skip empty rows
            if not row['Name'] and not row['Email'] and not row['Mobile Number']:
                continue
                
            # Validate email
            if row['Email']:
                email_valid, email_status, email_message = validate_email_address(row['Email'])
                df.at[idx, 'email_status'] = email_status
                df.at[idx, 'email_message'] = email_message
            
            # Validate phone
            if row['Mobile Number']:
                phone_valid, phone_status, phone_message = validate_phone_number(str(row['Mobile Number']))
                df.at[idx, 'phone_status'] = phone_status
                df.at[idx, 'phone_message'] = phone_message
                
                # Send WhatsApp for invalid emails if phone is valid
                if not email_valid and phone_valid and row['Name'] and row['Email']:
                    whatsapp_sent, whatsapp_status = send_whatsapp_notification(
                        row['Name'],
                        row['Mobile Number'],
                        row['Email']
                    )
                    df.at[idx, 'whatsapp_sent'] = 'YES' if whatsapp_sent else 'FAILED'
                    df.at[idx, 'whatsapp_status'] = whatsapp_status
        
        # Save processed file
        output_filename = 'validated_' + filename
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Convert DataFrame to dict for JSON response, handling NaN values
        results = df.replace({pd.NA: None}).to_dict('records')
        
        return jsonify({
            'message': 'File processed successfully',
            'download_filename': output_filename,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        return send_from_directory(directory=app.config['UPLOAD_FOLDER'],
                                 filename=filename,
                                 as_attachment=True,
                                 mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                                 
    except Exception as e:
        logger.error(f'Error downloading file: {str(e)}')
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/get-messages', methods=['GET'])
def get_messages():
    logger.info("/get-messages endpoint called")
    try:
        with open(MESSAGES_FILE, 'r') as file:
            messages = json.load(file)
            logger.info(f"Retrieved {len(messages)} messages")
            return jsonify({'messages': messages})
    except Exception as e:
        logger.error(f'Error retrieving messages: {str(e)}')
        return jsonify({'error': 'Error retrieving messages'}), 500

@app.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_webhook():
    try:
        logger.info("Received WhatsApp webhook")
        logger.info(f"Form data: {request.form}")
        
        # Get message details
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '').strip()
        
        if from_number and message_body:
            # Clean the phone number
            clean_number = from_number.replace('whatsapp:', '').replace('+', '')
            
            # Save the message
            save_message(
                name="WhatsApp User",
                phone=clean_number,
                old_email="",
                new_email=message_body,
                status='Received'
            )
            
            return jsonify({'success': True, 'message': 'Message saved successfully'})
        
        return jsonify({'success': False, 'message': 'Invalid message data'}), 400
        
    except Exception as e:
        logger.error(f'Error in webhook: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/messages')
def messages_page():
    return render_template('messages.html')

@app.route('/simulate-whatsapp', methods=['POST'])
def simulate_whatsapp():
    """Endpoint to simulate receiving a WhatsApp message"""
    try:
        data = request.get_json()
        phone = data.get('phone', '')
        message = data.get('message', '')
        
        if phone and message:
            # Save the message
            save_message(
                name="Test User",
                phone=phone,
                old_email="",
                new_email=message,
                status='Received'
            )
            return jsonify({'success': True, 'message': 'Message saved successfully'})
        
        return jsonify({'success': False, 'message': 'Missing phone or message'}), 400
        
    except Exception as e:
        logger.error(f'Error simulating WhatsApp message: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/send-whatsapp', methods=['POST'])
def send_single_whatsapp():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        
        if not all([name, phone, email]):
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
            
        # Format the WhatsApp message
        message = f"""Dear {name},

We noticed your email address ({email}) in our records may be incorrect. Please reply with your correct email address to ensure you receive important updates from American Hospital Dubai.

Thank you,
American Hospital Dubai"""

        # Send WhatsApp message
        try:
            # Format the phone number with proper international format
            whatsapp_to = f"whatsapp:+{phone}" if not phone.startswith('+') else f"whatsapp:{phone}"
            
            message = twilio_client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=whatsapp_to
            )
            logger.info(f"WhatsApp message sent successfully to {whatsapp_to}")
            return jsonify({
                'success': True, 
                'message_sid': message.sid,
                'status': 'WhatsApp message sent successfully'
            })
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Failed to send WhatsApp message: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500

@app.route('/webhook-forward', methods=['POST'])
def webhook_forward():
    try:
        data = request.get_json()
        
        # Extract form values from webhook.site data
        form_values = data.get('form_values', {})
        
        # Get relevant information
        from_number = form_values.get('From', '')
        message_body = form_values.get('Body', '')
        profile_name = form_values.get('ProfileName', '')
        
        if from_number and message_body:
            # Clean the phone number
            clean_number = from_number.replace('whatsapp:', '').replace('+', '')
            
            # Save the message
            save_message(
                name=profile_name or "WhatsApp User",
                phone=clean_number,
                old_email="",
                new_email=message_body,
                status='Received'
            )
            
            logger.info(f"Message saved from {profile_name} ({clean_number}): {message_body}")
            return jsonify({'success': True, 'message': 'Message saved successfully'})
        
        return jsonify({'success': False, 'message': 'Invalid message data'}), 400
        
    except Exception as e:
        logger.error(f'Error in webhook forward: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/test-twilio', methods=['GET'])
def test_twilio():
    try:
        # Try to fetch account info to verify credentials
        account = twilio_client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        return jsonify({
            'success': True,
            'message': 'Twilio connection successful',
            'account_name': account.friendly_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\nStarting server...")
    app.run(port=3000, debug=True)
