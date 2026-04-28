from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from functools import wraps
import json
import os
import uuid
from datetime import datetime
import re
import requests
import threading

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes
# ============================================================
# CONFIGURATION
# ============================================================

ID_INSTANCE = os.environ.get('GREEN_API_ID', '7107601889')
API_TOKEN_INSTANCE = os.environ.get('GREEN_API_TOKEN', '5e85cf0d650b451cb3ea6c15bfdde997ae51787937b149c198')
API_URL = f'https://7107.api.greenapi.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN_INSTANCE}'
ADMIN_WHATSAPP_NUMBER = os.environ.get('ADMIN_WHATSAPP', '2347034547179@c.us')
WHATSAPP_ENABLED = True

# Admin token from environment variable
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '7Xk9mP2nQ8rS5tU3vW7yZ4bC6dF8gH1jL9')

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)  # Enable CORS for all routes

# ============================================================
# FORCE CORS HEADERS - ADD THIS SECTION
# ============================================================

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Admin-Token'
    return response

# Handle OPTIONS preflight requests
@app.route('/api/orders', methods=['OPTIONS'])
@app.route('/api/orders/<order_id>', methods=['OPTIONS'])
@app.route('/api/orders/<order_id>/status', methods=['OPTIONS'])
def handle_options():
    response = jsonify({'status': 'ok'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Admin-Token'
    return response, 200

# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================

def admin_required(f):
    """Decorator to protect admin-only routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Token')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'success': False, 'message': 'Invalid or missing admin token'}), 401
        return f(*args, **kwargs)
    return decorated

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

DB_FILE = 'orders.json'
MIN_PRICE = 1000
MAX_PRICE = 3000
VALID_YAM_TYPES = ['Water Yam', 'Yellow Yam', 'White Yam']
VALID_STATUSES = ['pending', 'confirmed', 'dispatched', 'delivered', 'cancelled']

def load_orders():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading orders: {e}")
        return []

def save_orders(orders):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving orders: {e}")
        return False

def generate_order_id():
    return str(uuid.uuid4())[:8].upper()

# ============================================================
# WHATSAPP FUNCTION (keep your existing implementation)
# ============================================================

def send_whatsapp_notification(order):
    # Your existing code here - unchanged
    pass

# ============================================================
# PUBLIC ROUTES (no authentication)
# ============================================================

@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'NKs Yams Server running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/orders', methods=['POST'])
def create_new_order():
    # Your existing code here - unchanged
    pass

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_single_order(order_id):
    # Your existing code here - unchanged
    pass

# ============================================================
# PROTECTED ADMIN ROUTES (require authentication)
# ============================================================

@app.route('/api/orders', methods=['GET'])
@admin_required  # IMPORTANT: @admin_required comes AFTER @app.route
def get_all_orders():
    orders = load_orders()
    orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'count': len(orders), 'orders': orders})

@app.route('/api/orders/<order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    # Your existing code here - unchanged
    pass

@app.route('/api/orders/<order_id>', methods=['DELETE'])
@admin_required
def delete_order(order_id):
    # Your existing code here - unchanged
    pass

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == '__main__':
    print(f"🔐 Admin Token configured: {ADMIN_TOKEN[:10]}...")
    app.run(debug=True, host='0.0.0.0', port=5000)
