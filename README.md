# Hospital Email Validator

A Flask-based web application that validates hospital email addresses and integrates with WhatsApp for communication.

## Features

- WhatsApp integration using Twilio
- Email validation system
- Webhook endpoint for message processing
- Web interface for monitoring

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_WHATSAPP_NUMBER

3. Run the application:
```bash
python app.py
```

## Deployment

This application is configured for deployment on Render using the provided `render.yaml` configuration file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
