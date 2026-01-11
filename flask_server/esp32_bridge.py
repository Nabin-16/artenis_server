"""
ESP32 to Flask Bridge - Forwards WebSocket data from ESP32 to Flask server
This script runs on a computer connected to both ESP32 WiFi and internet
"""

import asyncio
import websockets
import socketio
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ESP32_IP = '192.168.4.1'  # ESP32 AP IP
ESP32_WS_URL = f'ws://{ESP32_IP}/ws'
FLASK_SERVER_URL = 'http://localhost:5000'  # Change to your Flask server URL

# Socket.IO client for Flask
sio = socketio.Client()

class ESP32Bridge:
    def __init__(self):
        self.esp32_connected = False
        self.flask_connected = False
        self.device_mappings = {}  # Map ESP32 client IDs to device IDs
    
    async def connect_to_esp32(self):
        """Connect to ESP32 WebSocket"""
        try:
            async with websockets.connect(ESP32_WS_URL) as websocket:
                self.esp32_connected = True
                logger.info(f'✅ Connected to ESP32 at {ESP32_WS_URL}')
                
                # Listen for messages from ESP32
                async for message in websocket:
                    await self.handle_esp32_message(message)
                    
        except Exception as e:
            logger.error(f'❌ ESP32 connection error: {e}')
            self.esp32_connected = False
            await asyncio.sleep(5)  # Wait before reconnecting
    
    async def handle_esp32_message(self, message):
        """Handle messages from ESP32 and forward to Flask"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', '')
            
            logger.debug(f'📨 Received from ESP32: {msg_type}')
            
            if msg_type == 'GPS':
                # Forward GPS data to Flask
                sio.emit('gps_data', {
                    'deviceId': data.get('deviceId'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'alt': data.get('alt'),
                    'speed': data.get('speed'),
                    'timestamp': data.get('timestamp')
                })
                logger.info(f'📍 Forwarded GPS data from {data.get("deviceId")}')
            
            elif msg_type == 'IMU':
                # Forward IMU data to Flask
                sio.emit('imu_data', {
                    'deviceId': data.get('deviceId'),
                    'accel': data.get('accel'),
                    'gyro': data.get('gyro'),
                    'mag': data.get('mag'),
                    'timestamp': data.get('timestamp')
                })
                logger.info(f'📊 Forwarded IMU data from {data.get("deviceId")}')
            
            elif msg_type == 'USER_DISCONNECT':
                # Forward disconnect notification
                sio.emit('device_disconnect', {
                    'deviceId': data.get('deviceId'),
                    'username': data.get('username')
                })
                logger.info(f'👋 Device disconnected: {data.get("deviceId")}')
            
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON from ESP32: {e}')
        except Exception as e:
            logger.error(f'Error handling ESP32 message: {e}')
    
    def connect_to_flask(self):
        """Connect to Flask Socket.IO server"""
        try:
            sio.connect(FLASK_SERVER_URL)
            self.flask_connected = True
            logger.info(f'✅ Connected to Flask server at {FLASK_SERVER_URL}')
        except Exception as e:
            logger.error(f'❌ Flask connection error: {e}')
            self.flask_connected = False

# Socket.IO event handlers
@sio.event
def connect():
    logger.info('✅ Socket.IO connection established')

@sio.event
def disconnect():
    logger.warning('⚠️ Socket.IO disconnected')

@sio.event
def connection_status(data):
    logger.info(f'Connection status: {data}')

async def main():
    """Main bridge loop"""
    bridge = ESP32Bridge()
    
    logger.info('=' * 50)
    logger.info('ESP32 to Flask Bridge Starting...')
    logger.info('=' * 50)
    logger.info(f'ESP32: {ESP32_WS_URL}')
    logger.info(f'Flask: {FLASK_SERVER_URL}')
    logger.info('=' * 50)
    
    # Connect to Flask first
    bridge.connect_to_flask()
    
    # Main loop - reconnect to ESP32 if disconnected
    while True:
        try:
            if not bridge.esp32_connected:
                logger.info('Attempting to connect to ESP32...')
                await bridge.connect_to_esp32()
            else:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info('Shutting down bridge...')
            sio.disconnect()
            break
        except Exception as e:
            logger.error(f'Bridge error: {e}')
            await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bridge stopped by user')
