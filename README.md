# IEEE Hackathon - Hat Detection & Tracking System

## Project Overview

This system automatically detects people wearing hats using a custom-trained YOLO AI model and tracks them with a servo-controlled camera mount. When a hat is detected, the system:
- Plays an audio alert through a Bluetooth speaker
- Automatically adjusts a servo motor to center the detected person in the camera frame
- Maintains tracking as the person moves
- Returns to home position after 3 seconds when no hats are detected

The system uses two ESP32 microcontrollers: one for video streaming (ESP32-CAM) and one for controlling the servo motor via WiFi. The main detection and tracking logic runs on a computer using Python and communicates with the hardware over the local network.

**Key Features:**
- Real-time hat detection with custom-trained YOLO v11 model (trained on 4000+ images)
- Automated servo tracking with smooth incremental movement
- WiFi-based motor control for wireless operation
- Audio alerts for immediate notification
- ByteTrack algorithm for consistent object tracking across frames

## Hardware Components Used

- **ESP32 (NodeMCU-32S)** - Main controller for servo motor - BOUGHT
- **ESP32-CAM** - Video streaming camera module - BOUGHT

- **180° Servo Motor** (SG90 or MG90S recommended) - BOUGHT

- **5V Power Supply** - USB power bank or wall adapter for powering ESP32 and servo - BOUGHT

- **Bluetooth Speaker** - Paired with computer for audio alerts

- Jumper wires for connections
- Breadboard (optional for testing)


## Libraries, APIs, and Frameworks Used

### Python Libraries
- **Ultralytics** (YOLO) - AI object detection framework
- **OpenCV** - Computer vision and video processing
- **NumPy** - Numerical computing for image processing
- **Requests** - HTTP communication with ESP32 over WiFi
- **Pygame** - Audio playback for alerts

### ESP32 Libraries (PlatformIO)
- **ESP32Servo** (v3.0.9) - Servo motor control
- **ArduinoJson** (v7.2.1) - JSON parsing for WiFi commands
- **WiFi** (built-in) - WiFi connectivity
- **WebServer** (built-in) - HTTP server for receiving commands

### Development Tools
- **PlatformIO** - ESP32 development and deployment
- **VS Code** - Primary IDE

## Setup Instructions

### 1. Hardware Assembly

1. **Connect Servo to ESP32:**
   - Servo VCC (Red) → 5V power supply
   - Servo GND (Brown) → GND (shared with ESP32)
   - Servo Signal (Orange) → ESP32 GPIO 14

2. **Power Setup:**
   - Connect ESP32 to 5V power supply or USB
   - Ensure servo has adequate power (external supply recommended for larger servos)

3. **Mount Camera:**
   - Attach ESP32-CAM to servo mount
   - Position for clear view of area to monitor

### 2. Software Installation

#### Install Python Dependencies
```bash
pip install ultralytics opencv-python numpy requests pygame
```

#### Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/IEEE-hackathon-hat-haters-.git
cd IEEE-hackathon-hat-haters-
```

### 3. ESP32 Configuration

#### Upload Servo Controller Code
1. Open project in VS Code with PlatformIO extension
2. navigate to wifi_servo_controller.cpp
3. Update WiFi credentials (lines 14-15):
   ```cpp
   const char* ssid = "YOUR_WIFI_NETWORK";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. Connect ESP32 via USB
5. Hold **BOOT** button on ESP32
6. Click **Upload** in PlatformIO
7. Release BOOT button when upload starts
8. Open **Serial Monitor** (115200 baud)
9. **Note the IP address** displayed (e.g., `192.168.1.100`)

#### Setup ESP32-CAM
1. Upload camera streaming firmware to ESP32-CAM(example given in IDE)
2. Note the streaming URL (e.g., `http://192.168.1.200:81/stream`)

### 4. Python Script Configuration

Edit `ultralytics_ai/wifi_hat_tracking_servo.py`:

```python
# Line 19 - Set ESP32-CAM stream URL
CAMERA_SOURCE = "http://192.168.1.200:81/stream"

# Line 22 - Set ESP32 controller IP (from Serial Monitor)
ESP32_IP = "192.168.1.100"

# Line 26 - Set audio alert file path
ALERT_AUDIO = "ultralytics_ai\\alert.mp3"
```

### 5. Audio Setup
1. Pair Bluetooth speaker with computer
2. Place `alert.mp3` file in `ultralytics_ai/` folder
3. Ensure speaker is set as default audio output

### 6. Run the System

```bash
cd IEEE-hackathon-hat-haters-
python ultralytics_ai/wifi_hat_tracking_servo.py
```

**Controls:**
- Press **'q'** to quit
- Press **'r'** to reset servo to home position (90°)

### 7. Testing & Calibration

1. **Test servo movement:** Press 'r' to see servo move to center
2. **Test detection:** Wear a hat and verify detection box appears
3. **Tune parameters** if needed:
   - `SERVO_STEP = 2` (adjust for movement speed)
   - `DEAD_ZONE_X = 50` (adjust for sensitivity)
   - `CONFIDENCE_THRESHOLD = 0.5` (adjust for detection accuracy)

### Network Requirements
- ESP32, ESP32-CAM, and computer must all be on the **same WiFi network**
- Ensure network allows device-to-device communication (not guest network)

### AI TRAINED ###
 - runs\detect\train_with_5000_hats_v2

## Team Members and Roles

**Team: Hat Haters**

- **Miguel Canales** - Full Stack

---

**IEEE Hackathon 2025**

