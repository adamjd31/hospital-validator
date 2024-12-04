from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Hospital Email Validator Platform - Welcome!"

@app.route('/api/webhook-forward', methods=['POST'])
def webhook_forward():
    try:
        data = request.get_json()
        # Process webhook data here
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Vercel serverless function handler
def handler(event, context):
    return app(event, context)

# For local development
if __name__ == '__main__':
    app.run(debug=True)
