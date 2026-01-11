# 🛰️ Artemis Server

**Real-time GPS & IMU Data Collection and Monitoring System**

Artemis Server is a Flask-based WebSocket server designed to collect, process, and visualize real-time GPS and IMU (Inertial Measurement Unit) data from ESP32 devices. It provides a web-based dashboard for monitoring multiple devices simultaneously with live location tracking and sensor data visualization.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [WebSocket Events](#websocket-events)
- [Configuration](#configuration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Artemis Server acts as a central hub for collecting sensor data from mobile devices (via ESP32 modules) and displaying it on a real-time web dashboard. The system is designed for:

- **Vehicle tracking** - Monitor GPS coordinates, speed, and altitude
- **Motion analysis** - Track acceleration, gyroscope, and magnetometer data
- **Multi-device monitoring** - Handle multiple ESP32 devices simultaneously
- **Real-time updates** - Instant data broadcasting via WebSockets
- **Historical data** - Store and retrieve device history

### Use Cases

- Fleet management and vehicle tracking
- Sports performance monitoring
- IoT device monitoring
- Research projects requiring sensor data collection
- Navigation and orientation tracking

---

## 🏗️ Architecture

The system consists of three main components:

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   ESP32 Device  │ ──WiFi─>│  ESP32 Bridge   │ ──HTTP──>│  Flask Server   │
│   (WiFi AP)     │         │   (Middleware)  │         │  (WebSocket)    │
│                 │         │                 │         │                 │
│  - GPS Data     │         │  - Forwards     │         │  - Stores Data  │
│  - IMU Data     │         │    Data         │         │  - Broadcasts   │
│  - User Info    │         │  - Translates   │         │  - Serves Web   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                                                   │
                                                                   │ WebSocket
                                                                   ▼
                                                         ┌─────────────────┐
                                                         │  Web Dashboard  │
                                                         │  (Browser)      │
                                                         │                 │
                                                         │  - Live Map     │
                                                         │  - Device List  │
                                                         │  - Sensor Data  │
                                                         └─────────────────┘
```

### Data Flow

1. **ESP32 Device** creates a WiFi access point and broadcasts sensor data via WebSocket
2. **ESP32 Bridge** connects to the ESP32's WiFi network and forwards data to the Flask server
3. **Flask Server** receives, processes, and stores the data, then broadcasts it to all connected dashboards
4. **Web Dashboard** displays real-time updates on an interactive map with device information

---

## ✨ Key Features

### Real-time Capabilities
- ✅ Live GPS tracking with map visualization
- ✅ Real-time IMU data (accelerometer, gyroscope, magnetometer)
- ✅ Instant device connection/disconnection notifications
- ✅ Multi-device simultaneous monitoring

### Data Management
- 📊 Historical data storage (last 1000 entries per device)
- 📍 Device activity tracking with automatic timeout (24-hour inactivity detection)
- 🔄 Auto-registration of new devices
- 💾 In-memory data storage with history retention

### Dashboard Features
- 🗺️ Interactive map with MapLibre GL JS
- 📱 Responsive device cards showing status and latest data
- 🎨 Modern dark-themed UI
- 🔴 Live connection status indicators

### Security & Configuration
- 🔒 Optional HTTPS support with SSL/TLS
- 🔑 Simple authentication system (extensible for production)
- ⚙️ Configurable host, port, and certificates
- 🌐 CORS support for cross-origin requests

---

## 🔧 Components

### 1. Flask Server (`app.py`)

The main server application that handles:
- HTTP REST API endpoints for device management
- WebSocket connections for real-time communication
- Data storage and broadcasting
- Device lifecycle management
- Authentication

**Key Endpoints:**
- `GET /` - Serves the dashboard
- `GET /api/devices` - Lists all active devices
- `GET /api/device/<id>` - Gets specific device data
- `GET /api/device/<id>/history` - Retrieves device history
- `POST /api/auth/login` - Authentication
- `POST /api/esp32/data` - Receives data from ESP32 bridge

### 2. ESP32 Bridge (`esp32_bridge.py`)

A middleware script that:
- Connects to ESP32 via WebSocket
- Connects to Flask server via Socket.IO
- Translates and forwards data between the two
- Handles reconnection logic

**Purpose:** ESP32 devices create their own WiFi network, so this bridge runs on a computer that can connect to both the ESP32's WiFi network and the internet to relay data to the Flask server.

### 3. Web Dashboard (`templates/dashboard.html`)

An interactive web interface featuring:
- Real-time map with device markers
- Device list with status indicators
- Live sensor data display
- Connection status monitoring

---

## 📦 Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- Network connectivity (WiFi for ESP32 bridge)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Nabin-16/artenis_server.git
cd artenis_server/flask_server
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

The required packages are:
- `Flask==3.0.0` - Web framework
- `flask-socketio==5.3.5` - WebSocket support
- `flask-cors==4.0.0` - Cross-Origin Resource Sharing
- `python-socketio==5.10.0` - Socket.IO implementation
- `eventlet==0.33.3` - Concurrent networking library
- `pyOpenSSL==23.3.0` - SSL/TLS support
- `websockets==12.0` - WebSocket client (for bridge)

---

## 💻 Usage

### Starting the Flask Server

**Basic usage (HTTP):**
```bash
python app.py
```

**Custom host and port:**
```bash
python app.py --host 0.0.0.0 --port 8080
```

**With HTTPS (auto-generates self-signed certificate):**
```bash
python app.py --https
```

**With custom SSL certificates:**
```bash
python app.py --https --cert /path/to/cert.pem --key /path/to/key.pem
```

The server will start and be accessible at:
- HTTP: `http://localhost:5000`
- HTTPS: `https://localhost:5000`

### Running the ESP32 Bridge

1. **Connect to ESP32 WiFi network** (usually named something like "ESP32-AP")

2. **Configure the bridge** by editing `esp32_bridge.py`:
   ```python
   ESP32_IP = '192.168.4.1'  # ESP32 AP IP address
   FLASK_SERVER_URL = 'http://your-server-ip:5000'  # Your Flask server URL
   ```

3. **Run the bridge:**
   ```bash
   python esp32_bridge.py
   ```

The bridge will:
- Connect to the ESP32 WebSocket server
- Connect to the Flask Socket.IO server
- Start forwarding data between them

### Accessing the Dashboard

Open your web browser and navigate to:
```
http://localhost:5000
```

You'll see:
- An interactive map (using MapLibre GL JS)
- List of connected devices
- Real-time GPS coordinates
- IMU sensor readings
- Connection status indicators

---

## 📡 API Documentation

### REST Endpoints

#### Get All Devices
```http
GET /api/devices
```

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "deviceId": "ESP32-001",
      "username": "User1",
      "status": "online",
      "connectedAt": "2024-01-11T10:30:00",
      "lastSeen": "2024-01-11T10:35:00",
      "gps": { "lat": 27.7172, "lon": 85.3240, "alt": 1400 },
      "imu": { "accel": {...}, "gyro": {...} }
    }
  ],
  "total": 1
}
```

#### Get Specific Device
```http
GET /api/device/<device_id>
```

**Response:**
```json
{
  "success": true,
  "device": {
    "deviceId": "ESP32-001",
    "username": "User1",
    "status": "online",
    "gps": { ... },
    "imu": { ... }
  }
}
```

#### Get Device History
```http
GET /api/device/<device_id>/history
```

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "type": "GPS",
      "data": { "lat": 27.7172, "lon": 85.3240 },
      "timestamp": "2024-01-11T10:30:00"
    }
  ]
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": "admin",
  "token": "dummy-token-use-jwt-in-production"
}
```

#### Receive ESP32 Data
```http
POST /api/esp32/data
Content-Type: application/json

{
  "type": "GPS",
  "deviceId": "ESP32-001",
  "username": "User1",
  "lat": 27.7172,
  "lon": 85.3240,
  "alt": 1400,
  "speed": 5.5,
  "accuracy": 10,
  "timestamp": "2024-01-11T10:30:00"
}
```

---

## 🔌 WebSocket Events

### Client → Server Events

#### Register Device
```javascript
socket.emit('register_device', {
  deviceId: 'ESP32-001',
  username: 'User1'
});
```

#### Send GPS Data
```javascript
socket.emit('gps_data', {
  deviceId: 'ESP32-001',
  lat: 27.7172,
  lon: 85.3240,
  alt: 1400,
  speed: 5.5,
  accuracy: 10,
  timestamp: '2024-01-11T10:30:00'
});
```

#### Send IMU Data
```javascript
socket.emit('imu_data', {
  deviceId: 'ESP32-001',
  accel: { x: 0.1, y: 0.2, z: 9.8 },
  gyro: { x: 0.01, y: 0.02, z: 0.03 },
  mag: { x: 20, y: 30, z: 40 },
  timestamp: '2024-01-11T10:30:00'
});
```

#### Disconnect Device
```javascript
socket.emit('device_disconnect', {
  deviceId: 'ESP32-001'
});
```

### Server → Client Events

#### Connection Status
```javascript
socket.on('connection_status', (data) => {
  console.log(data.status, data.message);
});
```

#### Active Devices List
```javascript
socket.on('active_devices', (data) => {
  console.log('Devices:', data.devices);
});
```

#### Device Registered
```javascript
socket.on('device_registered', (device) => {
  console.log('New device:', device);
});
```

#### GPS Update
```javascript
socket.on('gps_update', (data) => {
  console.log('GPS from', data.deviceId, data.gps);
});
```

#### IMU Update
```javascript
socket.on('imu_update', (data) => {
  console.log('IMU from', data.deviceId, data.imu);
});
```

#### Device Disconnected
```javascript
socket.on('device_disconnected', (data) => {
  console.log('Device offline:', data.deviceId);
});
```

---

## ⚙️ Configuration

### Server Configuration

Edit `app.py` to modify:

```python
# Secret key for sessions
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Device timeout (seconds)
DEVICE_TIMEOUT = 86400  # 24 hours

# Admin users
ADMIN_USERS = {
    'admin': 'admin123',
    'operator': 'operator123'
}
```

### Bridge Configuration

Edit `esp32_bridge.py` to modify:

```python
# ESP32 access point IP address
ESP32_IP = '192.168.4.1'

# Flask server URL (change to your server's IP/domain)
FLASK_SERVER_URL = 'http://localhost:5000'
```

### Command-line Arguments

```bash
python app.py --help
```

Options:
- `--host HOST` - Host to bind to (default: 0.0.0.0)
- `--port PORT` - Port to bind to (default: 5000)
- `--https` - Enable HTTPS
- `--cert FILE` - SSL certificate file
- `--key FILE` - SSL private key file

---

## 🔐 Security Considerations

### Current Implementation

⚠️ **This is a development/prototype implementation. For production use, implement proper security measures:**

1. **Authentication**: Currently uses simple username/password. Replace with:
   - JWT tokens
   - OAuth 2.0
   - API keys with rate limiting

2. **Secret Key**: Change the default Flask secret key:
   ```python
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')
   ```

3. **HTTPS**: Always use HTTPS in production:
   - Obtain proper SSL certificates (Let's Encrypt)
   - Don't use self-signed certificates in production

4. **Data Validation**: Add input validation for all endpoints

5. **CORS**: Restrict CORS to specific origins:
   ```python
   CORS(app, origins=['https://yourdomain.com'])
   ```

6. **Rate Limiting**: Implement rate limiting to prevent abuse

7. **Database**: Use a proper database instead of in-memory storage:
   - PostgreSQL with TimescaleDB for time-series data
   - MongoDB for flexible schema
   - Redis for caching

---

## 🐛 Troubleshooting

### Server won't start

**Problem:** `Address already in use`
**Solution:** Change the port or kill the process using port 5000:
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
```

### Bridge can't connect to ESP32

**Problem:** Connection refused to ESP32
**Solution:**
1. Verify you're connected to ESP32's WiFi network
2. Check ESP32 IP address (usually 192.168.4.1)
3. Ensure ESP32 WebSocket server is running
4. Try pinging the ESP32: `ping 192.168.4.1`

### No data appearing on dashboard

**Problem:** Dashboard shows no devices
**Solution:**
1. Check browser console for errors (F12)
2. Verify WebSocket connection is established
3. Check server logs for incoming data
4. Ensure bridge is running and connected

### HTTPS certificate errors

**Problem:** Browser shows security warning
**Solution:**
- For development: Accept the self-signed certificate
- For production: Use proper SSL certificates from a CA (Let's Encrypt)

---

## 📝 Data Formats

### GPS Data Structure
```json
{
  "lat": 27.7172,      // Latitude (decimal degrees)
  "lon": 85.3240,      // Longitude (decimal degrees)
  "alt": 1400,         // Altitude (meters)
  "speed": 5.5,        // Speed (m/s or km/h depending on source)
  "accuracy": 10,      // Accuracy (meters)
  "timestamp": "ISO 8601 datetime string"
}
```

### IMU Data Structure
```json
{
  "accel": {           // Accelerometer (m/s²)
    "x": 0.1,
    "y": 0.2,
    "z": 9.8
  },
  "gyro": {            // Gyroscope (rad/s or deg/s)
    "x": 0.01,
    "y": 0.02,
    "z": 0.03
  },
  "mag": {             // Magnetometer (μT)
    "x": 20,
    "y": 30,
    "z": 40
  },
  "alpha": 0,          // Rotation around Z axis (optional)
  "beta": 0,           // Rotation around X axis (optional)
  "gamma": 0,          // Rotation around Y axis (optional)
  "timestamp": "ISO 8601 datetime string"
}
```

---

## 🤝 Contributing

Contributions are welcome! This project can be improved in many ways:

- Add database persistence
- Implement proper authentication (JWT)
- Add data export functionality
- Create mobile app dashboard
- Add alerts and notifications
- Improve UI/UX
- Add unit tests

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

## 👥 Credits

Developed by Nabin-16

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Happy Tracking! 🛰️**
