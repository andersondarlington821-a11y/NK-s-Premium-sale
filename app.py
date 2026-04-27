"""
NK's Yams - Python Backend Server with WhatsApp Notifications
Using direct Green API calls with requests library
"""

# ============================================================
# IMPORTS
# ============================================================

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime
import re
import requests
import threading

# ============================================================
# GREEN API WHATSAPP CONFIGURATION
# ============================================================

# Your Green API credentials (the sender WhatsApp number)
ID_INSTANCE = '7107601889'
API_TOKEN_INSTANCE = '5e85cf0d650b451cb3ea6c15bfdde997ae51787937b149c198'
API_URL = f'https://7107.api.greenapi.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN_INSTANCE}'

# The WhatsApp number that will RECEIVE order notifications (your personal number)
# Format: country code without '+' + '@c.us'
ADMIN_WHATSAPP_NUMBER = '2347034547179@c.us'  # 👈 Change to your personal WhatsApp

# Enable/disable WhatsApp notifications
WHATSAPP_ENABLED = True

# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Database file
DB_FILE = 'orders.json'

# Price limits
MIN_PRICE = 1000
MAX_PRICE = 3000

# Valid yam types
VALID_YAM_TYPES = ['Water Yam', 'Yellow Yam', 'White Yam']
VALID_STATUSES = ['pending', 'confirmed', 'dispatched', 'delivered', 'cancelled']

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def load_orders():
    """Load all orders from JSON file"""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading orders: {e}")
        return []

def save_orders(orders):
    """Save orders to JSON file"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving orders: {e}")
        return False

def generate_order_id():
    """Generate unique 8-character order ID"""
    return str(uuid.uuid4())[:8].upper()

# ============================================================
# WHATSAPP NOTIFICATION FUNCTION (using requests)
# ============================================================

def send_whatsapp_notification(order):
    """
    Send order details via WhatsApp using Green API (direct POST request)
    """
    if not WHATSAPP_ENABLED:
        print("📱 WhatsApp notifications are disabled.")
        return
    
    # Format the message with emojis and line breaks
    message = (
        f"🛒 *NEW ORDER RECEIVED!*\n\n"
        f"📋 *Order ID:* #{order['orderId']}\n"
        f"👤 *Customer:* {order['customerName']}\n"
        f"📞 *Phone:* {order['phone']}\n"
        f"📍 *Address:* {order['deliveryAddress']}\n"
        f"🍠 *Yam Type:* {order['yamType']}\n"
        f"💰 *Price per tuber:* ₦{order['pricePerTuber']:,}\n"
        f"📦 *Quantity:* {order['quantity']}\n"
        f"💵 *Total Amount:* ₦{order['totalPrice']:,}\n"
        f"⏰ *Order Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"_Use admin dashboard to manage this order._"
    )
    
    # Prepare the payload
    payload = {
        "chatId": ADMIN_WHATSAPP_NUMBER,
        "message": message
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Send POST request to Green API
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('idMessage'):
                print(f"✅ WhatsApp notification sent for Order #{order['orderId']}")
            else:
                print(f"⚠️ WhatsApp response: {result}")
        else:
            print(f"❌ WhatsApp API error {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⚠️ WhatsApp request timed out, but order was saved.")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp notification: {e}")

# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate_order(data):
    """Validate all order fields"""
    errors = []
    
    name = data.get('customerName', '').strip()
    if not name or len(name) < 2:
        errors.append('Customer name is required (min 2 characters)')
    
    phone = data.get('phone', '').strip()
    if not phone or not re.match(r'^[0-9]{7,15}$', phone):
        errors.append('Phone number must be 7-15 digits')
    
    address = data.get('deliveryAddress', '').strip()
    if not address or len(address) < 5:
        errors.append('Delivery address is required (min 5 characters)')
    
    yam_type = data.get('yamType')
    if not yam_type or yam_type not in VALID_YAM_TYPES:
        errors.append(f'Yam type must be one of: {", ".join(VALID_YAM_TYPES)}')
    
    price = data.get('pricePerTuber')
    if not price or not isinstance(price, (int, float)) or price < MIN_PRICE or price > MAX_PRICE:
        errors.append(f'Price must be between ₦{MIN_PRICE} and ₦{MAX_PRICE}')
    
    quantity = data.get('quantity')
    if not quantity or not isinstance(quantity, int) or quantity < 1:
        errors.append('Quantity must be at least 1')
    
    return errors

# ============================================================
# API ROUTES
# ============================================================

@app.route('/')
def serve_index():
    """Serve customer order form"""
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any file from public folder"""
    return send_from_directory('public', filename)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'message': 'NKs Yams Server with WhatsApp',
        'timestamp': datetime.now().isoformat(),
        'whatsapp_enabled': WHATSAPP_ENABLED
    })

@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    """Get all orders (admin dashboard)"""
    orders = load_orders()
    orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'count': len(orders), 'orders': orders})

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_single_order(order_id):
    """Get a specific order by ID"""
    orders = load_orders()
    order = next((o for o in orders if o.get('orderId') == order_id.upper()), None)
    if order:
        return jsonify({'success': True, 'order': order})
    return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders', methods=['POST'])
def create_new_order():
    """Create a new order (customer submits form)"""
    try:
        data = request.get_json()
        
        print(f"\n📝 New order from: {data.get('customerName', 'Unknown')}")
        
        # Validate input
        errors = validate_order(data)
        if errors:
            return jsonify({'success': False, 'message': errors[0]}), 400
        
        # Create order object
        new_order = {
            'orderId': generate_order_id(),
            'customerName': data['customerName'].strip(),
            'phone': data['phone'].strip(),
            'deliveryAddress': data['deliveryAddress'].strip(),
            'yamType': data['yamType'],
            'pricePerTuber': data['pricePerTuber'],
            'quantity': data['quantity'],
            'totalPrice': data['pricePerTuber'] * data['quantity'],
            'status': 'pending',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': None
        }
        
        # Save to database
        orders = load_orders()
        orders.append(new_order)
        save_orders(orders)
        
        print(f"✅ Order #{new_order['orderId']} saved")
        
        # Send WhatsApp notification (in background thread to not block response)
        if WHATSAPP_ENABLED:
            thread = threading.Thread(target=send_whatsapp_notification, args=(new_order,))
            thread.daemon = True
            thread.start()
            print(f"📱 WhatsApp notification queued")
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Order placed successfully! Check WhatsApp for confirmation.',
            'orderId': new_order['orderId'],
            'order': new_order
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating order: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orders/<order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """Update order status (admin dashboard)"""
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in VALID_STATUSES:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    orders = load_orders()
    order_id = order_id.upper()
    
    for order in orders:
        if order.get('orderId') == order_id:
            old_status = order['status']
            order['status'] = new_status
            order['updatedAt'] = datetime.now().isoformat()
            save_orders(orders)
            print(f"📦 Order #{order_id} status: {old_status} → {new_status}")
            return jsonify({'success': True, 'message': 'Status updated', 'order': order})
    
    return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete an order (admin dashboard)"""
    orders = load_orders()
    order_id = order_id.upper()
    original_count = len(orders)
    orders = [o for o in orders if o.get('orderId') != order_id]
    
    if len(orders) == original_count:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    save_orders(orders)
    print(f"🗑️ Order #{order_id} deleted")
    return jsonify({'success': True, 'message': 'Order deleted'})

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("   🌿 NK's YAMS BACKEND WITH WHATSAPP 🌿")
    print("="*50)
    print("\n📋 Configuration:")
    print(f"   • Price Range: ₦{MIN_PRICE:,} - ₦{MAX_PRICE:,}")
    print(f"   • WhatsApp Notifications: {'ENABLED' if WHATSAPP_ENABLED else 'DISABLED'}")
    print(f"   • Receiver Number: {ADMIN_WHATSAPP_NUMBER}")
    print(f"\n📍 Access:")
    print(f"   • Customer Page: http://localhost:5000")
    print(f"   • Admin Dashboard: http://localhost:5000/admin.html")
    print(f"   • Track Order: http://localhost:5000/track.html")
    print(f"   • Health Check: http://localhost:5000/health")
    print("\n" + "="*50)
    print("✅ Server running! Waiting for orders...")
    print("💡 WhatsApp notifications will be sent when orders are placed.\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    app = Flask(__name__)
