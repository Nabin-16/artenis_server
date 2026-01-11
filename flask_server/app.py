"""
Flask Server with WebSocket support for receiving GPS/IMU data from ESP32
Supports HTTPS and real-time data broadcasting to connected dashboards
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import logging
from datetime import datetime
import ssl

# Configure logging
logging.basicConfig(level=logging.INF
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
CORS(app)

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active devices and their data
active_devices = {}
device_history = {}
DEVICE_TIMEOUT = 86400  # 24 hours (86400 seconds) before marking device offline

# Background thread to check for inactive devices
def check_device_activity():
    while True:
        socketio.sleep(10)
        try:
            now = datetime.now()
            to_remove = []
            
            for device_id, device in active_devices.items():
                if device['status'] == 'online':
                    last_seen = datetime.fromisoformat(device['lastSeen'])
                    if (now - last_seen).total_seconds() > DEVICE_TIMEOUT:
                        device['status'] = 'offline'
                        logger.info(f'Device timeout: {device_id}')
                        to_remove.append(device_id)
                        
                        socketio.emit('device_disconnected', {
                            'deviceId': device_id,
                            'username': device['username']
                        })
            
            # Optional: Remove completely instead of just marking offline
            for device_id in to_remove:
                del active_devices[device_id]
                
        except Exception as e:
            logger.error(f'Error in watchdog: {e}')

# Start watchdog
socketio.start_background_task(check_device_activity)

# Authentication (simple example - use proper auth in production)
ADMIN_USERS = {
    'admin': 'admin123',
    'operator': 'operator123'
}

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all active devices"""
    return jsonify({
        'success': True,
        'devices': list(active_devices.values()),
        'total': len(active_devices)
    })

@app.route('/api/device/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device data"""
    if device_id in active_devices:
        return jsonify({
            'success': True,
            'device': active_devices[device_id]
        })
    return jsonify({
        'success': False,
        'error': 'Device not found'
    }), 404

@app.route('/api/device/<device_id>/history', methods=['GET'])
def get_device_history(device_id):
    """Get device history"""
    if device_id in device_history:
        return jsonify({
            'success': True,
            'history': device_history[device_id][-100:]  # Last 100 records
        })
    return jsonify({
        'success': False,
        'error': 'No history found'
    }), 404

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple authentication endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in ADMIN_USERS and ADMIN_USERS[username] == password:
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': username,
            'token': 'dummy-token-use-jwt-in-production'
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid credentials'
    }), 401

@app.route('/api/esp32/data', methods=['POST'])
def receive_esp32_data():
    """Receive data from ESP32 and broadcast to dashboards"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        msg_type = data.get('type')
        
        if msg_type == 'USER_CONNECTED':
            device_id = data.get('deviceId')
            username = data.get('username')
            
            device_info = {
                'deviceId': device_id,
                'username': username,
                'status': 'online',
                'connectedAt': datetime.now().isoformat(),
                'lastSeen': datetime.now().isoformat(),
                'gps': None,
                'imu': None
            }
            
            active_devices[device_id] = device_info
            
            if device_id not in device_history:
                device_history[device_id] = []
            
            logger.info(f'Device registered via ESP32: {username} ({device_id})')
            
            # Broadcast to all connected dashboards
            socketio.emit('device_registered', device_info)
            
        elif msg_type == 'USER_DISCONNECT':
            device_id = data.get('deviceId')
            if device_id in active_devices:
                active_devices[device_id]['status'] = 'offline'
                # Remove from list completely to clean up UI
                del active_devices[device_id]
                
                socketio.emit('device_disconnected', {
                    'deviceId': device_id, 
                    'username': data.get('username')
                })
                logger.info(f'Device explicitly disconnected: {device_id}')

        elif msg_type == 'GPS':
            device_id = data.get('deviceId')
            username = data.get('username', 'Unknown')
            
            # Auto-register device if not exists
            if device_id not in active_devices:
                active_devices[device_id] = {
                    'deviceId': device_id,
                    'username': username,
                    'status': 'online',
                    'connectedAt': datetime.now().isoformat(),
                    'lastSeen': datetime.now().isoformat(),
                    'gps': None,
                    'imu': None
                }
                device_history[device_id] = []
                socketio.emit('device_registered', active_devices[device_id])
                logger.info(f'Auto-registered device: {username} ({device_id})')
            
            gps_info = {
                'lat': data.get('lat'),
                'lon': data.get('lon'),
                'alt': data.get('alt'),
                'speed': data.get('speed'),
                'accuracy': data.get('accuracy'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            active_devices[device_id]['gps'] = gps_info
            active_devices[device_id]['lastSeen'] = datetime.now().isoformat()
            
            # Store in history
            history_entry = {
                'type': 'GPS',
                'data': gps_info,
                'timestamp': datetime.now().isoformat()
            }
            device_history[device_id].append(history_entry)
            
            if len(device_history[device_id]) > 1000:
                device_history[device_id] = device_history[device_id][-1000:]
            
            # Broadcast to dashboards
            socketio.emit('gps_update', {
                'deviceId': device_id,
                'username': active_devices[device_id]['username'],
                'gps': gps_info
            })
                
        elif msg_type == 'IMU':
            device_id = data.get('deviceId')
            username = data.get('username', 'Unknown')
            
            # Auto-register device if not exists
            if device_id not in active_devices:
                active_devices[device_id] = {
                    'deviceId': device_id,
                    'username': username,
                    'status': 'online',
                    'connectedAt': datetime.now().isoformat(),
                    'lastSeen': datetime.now().isoformat(),
                    'gps': None,
                    'imu': None
                }
                device_history[device_id] = []
                socketio.emit('device_registered', active_devices[device_id])
                logger.info(f'Auto-registered device: {username} ({device_id})')
            
            imu_info = {
                'accel': data.get('accel'),
                'gyro': data.get('gyro'),
                'mag': data.get('mag'),
                'alpha': data.get('alpha'),
                'beta': data.get('beta'),
                'gamma': data.get('gamma'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            active_devices[device_id]['imu'] = imu_info
            active_devices[device_id]['lastSeen'] = datetime.now().isoformat()
            
            # Store in history
            history_entry = {
                'type': 'IMU',
                'data': imu_info,
                'timestamp': datetime.now().isoformat()
            }
            device_history[device_id].append(history_entry)
            
            # Broadcast to dashboards
            socketio.emit('imu_update', {
                'deviceId': device_id,
                'username': active_devices[device_id]['username'],
                'imu': imu_info
            })
        
        return jsonify({'success': True, 'message': 'Data received and broadcasted'})
        
    except Exception as e:
        logger.error(f'Error receiving ESP32 data: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected', 'message': 'Connected to server'})
    
    # Send current active devices to newly connected client
    emit('active_devices', {'devices': list(active_devices.values())})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('register_device')
def handle_device_registration(data):
    """Handle device registration"""
    try:
        device_id = data.get('deviceId')
        username = data.get('username')
        
        device_info = {
            'deviceId': device_id,
            'username': username,
            'status': 'online',
            'connectedAt': datetime.now().isoformat(),
            'lastSeen': datetime.now().isoformat(),
            'gps': None,
            'imu': None
        }
        
        active_devices[device_id] = device_info
        
        # Initialize history
        if device_id not in device_history:
            device_history[device_id] = []
        
        logger.info(f'Device registered: {device_id} ({username})')
        
        # Broadcast to all clients
        emit('device_registered', device_info, broadcast=True)
        emit('registration_success', {'message': 'Device registered successfully'})
        
    except Exception as e:
        logger.error(f'Error registering device: {str(e)}')
        emit('error', {'message': 'Registration failed'})

@socketio.on('gps_data')
def handle_gps_data(data):
    """Handle GPS data from devices"""
    try:
        device_id = data.get('deviceId')
        
        if device_id in active_devices:
            gps_info = {
                'lat': data.get('lat'),
                'lon': data.get('lon'),
                'alt': data.get('alt'),
                'speed': data.get('speed'),
                'accuracy': data.get('accuracy'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            active_devices[device_id]['gps'] = gps_info
            active_devices[device_id]['lastSeen'] = datetime.now().isoformat()
            
            # Store in history
            history_entry = {
                'type': 'GPS',
                'data': gps_info,
                'timestamp': datetime.now().isoformat()
            }
            device_history[device_id].append(history_entry)
            
            # Keep only last 1000 entries
            if len(device_history[device_id]) > 1000:
                device_history[device_id] = device_history[device_id][-1000:]
            
            # Broadcast to all dashboard clients
            emit('gps_update', {
                'deviceId': device_id,
                'username': active_devices[device_id]['username'],
                'gps': gps_info
            }, broadcast=True)
            
            logger.debug(f'GPS data received from {device_id}')
        
    except Exception as e:
        logger.error(f'Error handling GPS data: {str(e)}')

@socketio.on('imu_data')
def handle_imu_data(data):
    """Handle IMU data from devices"""
    try:
        device_id = data.get('deviceId')
        
        if device_id in active_devices:
            imu_info = {
                'accel': data.get('accel'),
                'gyro': data.get('gyro'),
                'mag': data.get('mag'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            active_devices[device_id]['imu'] = imu_info
            active_devices[device_id]['lastSeen'] = datetime.now().isoformat()
            
            # Store in history
            history_entry = {
                'type': 'IMU',
                'data': imu_info,
                'timestamp': datetime.now().isoformat()
            }
            device_history[device_id].append(history_entry)
            
            # Broadcast to all dashboard clients
            emit('imu_update', {
                'deviceId': device_id,
                'username': active_devices[device_id]['username'],
                'imu': imu_info
            }, broadcast=True)
            
            logger.debug(f'IMU data received from {device_id}')
        
    except Exception as e:
        logger.error(f'Error handling IMU data: {str(e)}')

@socketio.on('device_disconnect')
def handle_device_disconnect(data):
    """Handle device disconnect notification"""
    try:
        device_id = data.get('deviceId')
        
        if device_id in active_devices:
            active_devices[device_id]['status'] = 'offline'
            active_devices[device_id]['disconnectedAt'] = datetime.now().isoformat()
            
            # Broadcast to all clients
            emit('device_disconnected', {
                'deviceId': device_id,
                'username': active_devices[device_id]['username']
            }, broadcast=True)
            
            logger.info(f'Device disconnected: {device_id}')
        
    except Exception as e:
        logger.error(f'Error handling device disconnect: {str(e)}')

@socketio.on('enable_sharing')
def handle_enable_sharing(data):
    """Handle data sharing toggle"""
    try:
        device_id = data.get('deviceId')
        enabled = data.get('enabled', False)
        
        if device_id in active_devices:
            active_devices[device_id]['dataSharingEnabled'] = enabled
            
            logger.info(f'Data sharing {"enabled" if enabled else "disabled"} for {device_id}')
            emit('sharing_status_changed', {
                'deviceId': device_id,
                'enabled': enabled
            }, broadcast=True)
        
    except Exception as e:
        logger.error(f'Error handling sharing toggle: {str(e)}')

def run_server(host='0.0.0.0', port=5000, use_https=False, cert_file=None, key_file=None):
    """Run the Flask server with optional HTTPS"""
    if use_https:
        if not cert_file or not key_file:
            logger.error('HTTPS enabled but certificate files not provided')
            logger.info('Generating self-signed certificate...')
            # For production, use proper SSL certificates
            import subprocess
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-nodes', '-out', 'cert.pem', '-keyout', 'key.pem',
                '-days', '365', '-subj', '/CN=localhost'
            ])
            cert_file = 'cert.pem'
            key_file = 'key.pem'
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        logger.info(f'Starting HTTPS server on https://{host}:{port}')
        socketio.run(app, host=host, port=port, ssl_context=context, debug=False)
    else:
        logger.info(f'Starting HTTP server on http://{host}:{port}')
        socketio.run(app, host=host, port=port, debug=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Artemis Flask Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--https', action='store_true', help='Enable HTTPS')
    parser.add_argument('--cert', help='SSL certificate file')
    parser.add_argument('--key', help='SSL private key file')
    
    args = parser.parse_args()
    
    run_server(
        host=args.host,
        port=args.port,
        use_https=args.https,
        cert_file=args.cert,
        key_file=args.key
    )
