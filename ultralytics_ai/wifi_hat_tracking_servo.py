"""
Complete Hat Detection System with WiFi Servo Control and Audio Alerts
- Detects hats with YOLO
- Sends servo position commands to ESP32 over WiFi
- Plays audio alerts when hats are detected
- Uses 180-degree servo for precise position control
"""

from ultralytics import YOLO
import numpy as np
import cv2
import requests
import json
import time
from audio_alert import AudioAlert

# Configuration
MODEL_PATH = "..\\runs\\detect\\train_with_5000_hats_v2\\weights\\best.pt"
CAMERA_SOURCE = "http://172.16.159.249:81/stream"  # http://172.16.159.248:81/stream

# ESP32 WiFi settings
ESP32_IP = "172.16.159.248"  # Change to your ESP32's IP address
ESP32_PORT = 80
ESP32_URL = f"http://{ESP32_IP}:{ESP32_PORT}/servo"

# Audio alert settings
ALERT_AUDIO = "ultralytics_ai\\alert.mp3"  # Your alert sound file
ALERT_COOLDOWN = 10  # Seconds between alerts

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
DEAD_ZONE_X = 50  # Pixels tolerance before moving servo
DEAD_ZONE_Y = 50

# Servo settings
SERVO_HOME = 90  # Center position (0-180 degrees)
SERVO_MIN = 0    # Leftmost position
SERVO_MAX = 180  # Rightmost position
SERVO_STEP = 2   # Degrees to move per frame (smaller = smoother, larger = faster)


class ESP32ServoController:
    """Control ESP32 servo over WiFi with position tracking"""
    
    def __init__(self, esp32_url, home_position=90, timeout=1.0):
        self.url = esp32_url
        self.timeout = timeout
        self.connected = False
        self.last_command = None
        self.command_count = 0
        
        # Servo position tracking
        self.servo_position = home_position 
        self.home_position = home_position
        self.target_position = home_position
        self.last_update_time = time.time()
        
        # Return home delay
        self.no_hat_start_time = None
        self.return_home_delay = 3.0  
        
    def test_connection(self):
        """Test if ESP32 is reachable"""
        try:
            response = requests.get(f"http://{ESP32_IP}:{ESP32_PORT}/status", timeout=2)
            self.connected = response.status_code == 200
            return self.connected
        except:
            self.connected = False
            return False
    
    def send_servo_position(self, position):
        """
        Send servo position command to ESP32
        
        Parameters:
        -----------
        position : int
            Servo angle (0-180 degrees)
        
        Returns:
        --------
        bool : True if command sent successfully
        """
        
        position = max(SERVO_MIN, min(SERVO_MAX, position))
        
        try:
            data = {
                'position': position
            }
            
            response = requests.post(
                self.url, 
                json=data, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.servo_position = position
                self.last_command = data
                self.command_count += 1
                self.connected = True
                self.last_update_time = time.time()
                return True
            else:
                print(f"⚠️  ESP32 returned status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("⚠️  ESP32 connection timeout")
            self.connected = False
            return False
        except requests.exceptions.ConnectionError:
            if self.connected:  
                print("⚠️  ESP32 connection lost")
            self.connected = False
            return False
        except Exception as e:
            print(f"⚠️  Error sending command: {e}")
            return False
    
    def move_to_position(self, target_position, step_size=None):
        """
        Move servo towards target position
        
        Parameters:
        -----------
        target_position : int
            Desired servo angle (0-180)
        step_size : int, optional
            Max degrees to move per call (for smooth movement)
        
        Returns:
        --------
        bool : True if command sent successfully
        """
        
        if step_size is None:
            return self.send_servo_position(target_position)
        else:
            diff = target_position - self.servo_position
            
            if abs(diff) <= step_size:
                return self.send_servo_position(target_position)
            else:
                new_position = self.servo_position + (step_size if diff > 0 else -step_size)
                return self.send_servo_position(new_position)
    
    def return_to_home(self):
        """
        Return servo to home position (center) after delay
        
        Returns:
        --------
        bool : True if returning home, False if at home or waiting
        """
        
        current_time = time.time()
        
        if self.no_hat_start_time is None:
            self.no_hat_start_time = current_time
            return False  
        
        elapsed = current_time - self.no_hat_start_time
        if elapsed < self.return_home_delay:
            return False  # Still waiting
        
        if abs(self.servo_position - self.home_position) <= 2:
            self.no_hat_start_time = None
            return False
        else:
            self.send_servo_position(self.home_position)
            return True
    
    def cancel_return_home(self):
        """Cancel return to home timer (when hat is detected again)"""
        self.no_hat_start_time = None
    
    def reset_to_home(self):
        """Force servo to home position immediately"""
        self.servo_position = self.home_position
        self.send_servo_position(self.home_position)
        print(f"✓ Servo reset to home position ({self.home_position}°)")


class HatTracker:
    """Track detected hats and calculate servo control commands"""
    
    def __init__(self, frame_width, frame_height, servo_home=90, servo_range=180):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
        self.servo_home = servo_home
        self.servo_min = max(0, servo_home - servo_range // 2)
        self.servo_max = min(180, servo_home + servo_range // 2)
        
    def get_detected_hats(self, results):
        """Extract hat detections from YOLO results"""
        #hats sort by confidence
        hats = []
        
        if len(results) == 0 or results[0].boxes is None:
            return hats
        
        boxes = results[0].boxes
        
        for box in boxes:
            conf = float(box.conf[0])
            
            if conf >= CONFIDENCE_THRESHOLD:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                width = x2 - x1
                height = y2 - y1
                area = width * height
                
                hat_info = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'center': [cx, cy],
                    'confidence': conf,
                    'area': int(area),
                    'width': int(width),
                    'height': int(height)
                }
                
                hats.append(hat_info)
        
        hats.sort(key=lambda x: x['confidence'], reverse=True)
        return hats
    
    def calculate_servo_position(self, hat_center, current_servo_pos, dead_zone_x=50):
        """
        Calculate servo position needed to center a hat
        
        Parameters:
        -----------
        hat_center : tuple
            (x, y) center of hat in frame
        current_servo_pos : int
            Current servo angle
        dead_zone_x : int
            Pixels tolerance before moving
        
        Returns:
        --------
        dict : Servo command info
        """
        cx, cy = hat_center
        
        offset_x = cx - self.center_x
        offset_y = cy - self.center_y
        
        needs_adjustment = abs(offset_x) > dead_zone_x
        
        if not needs_adjustment:
            return {
                'target_position': current_servo_pos,
                'offset_x': int(offset_x),
                'offset_y': int(offset_y),
                'needs_adjustment': False,
                'direction': 'centered'
            }
        
        pixel_to_degree = (self.servo_max - self.servo_min) / self.frame_width
        servo_adjustment = -offset_x * pixel_to_degree  # REVERSED direction
        
        target_position = current_servo_pos + servo_adjustment
        
        target_position = max(self.servo_min, min(self.servo_max, target_position))
        
        direction = 'right' if servo_adjustment > 0 else 'left' if servo_adjustment < 0 else 'centered'
        
        return {
            'target_position': int(target_position),
            'offset_x': int(offset_x),
            'offset_y': int(offset_y),
            'needs_adjustment': needs_adjustment,
            'direction': direction,
            'adjustment': int(servo_adjustment)
        }
    
    def select_target_hat(self, hats):
        """Select which hat to track (largest by area)"""
        if not hats:
            return None
        return max(hats, key=lambda x: x['area'])


def draw_tracking_overlay(frame, hats, target_hat, servo_command, esp32_connected, servo_position):
    """Draw visual feedback on the frame"""
    
    # Draw all detected hats
    for i, hat in enumerate(hats):
        x1, y1, x2, y2 = hat['bbox']
        cx, cy = hat['center']
        
        color = (0, 255, 0) if hat == target_hat else (0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, (cx, cy), 5, color, -1)
        
        label = f"Hat {i+1}: {hat['confidence']:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2
    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 0, 255), 2)
    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 0, 255), 2)
    
    cv2.rectangle(frame, 
                  (center_x - DEAD_ZONE_X, center_y - DEAD_ZONE_Y),
                  (center_x + DEAD_ZONE_X, center_y + DEAD_ZONE_Y),
                  (255, 0, 0), 1)
    
    # Display servo command info
    if servo_command and servo_command['needs_adjustment']:
        status_text = f"Target: {servo_command['target_position']}° ({servo_command['direction']})"
        cv2.putText(frame, status_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        offset_text = f"Offset: X={servo_command['offset_x']} Y={servo_command['offset_y']}"
        cv2.putText(frame, offset_text, (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    elif len(hats) == 0:
        cv2.putText(frame, "RETURNING HOME...", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
    else:
        cv2.putText(frame, "CENTERED!", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    position_text = f"Servo: {servo_position}° / {SERVO_HOME}° (home)"
    cv2.putText(frame, position_text, (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    # bar_x = 10
    # bar_y = h - 50
    # bar_width = 360
    # bar_height = 20
    
    # cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
    
    # home_x = bar_x + int((SERVO_HOME / 180) * bar_width)
    # cv2.line(frame, (home_x, bar_y), (home_x, bar_y + bar_height), (0, 255, 0), 2)
    
    # # Draw current position marker
    # pos_x = bar_x + int((servo_position / 180) * bar_width)
    # cv2.circle(frame, (pos_x, bar_y + bar_height // 2), 8, (0, 255, 255), -1)
    
    # # Labels
    # cv2.putText(frame, "0°", (bar_x, bar_y - 5), 
    #             cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    # cv2.putText(frame, "180°", (bar_x + bar_width - 30, bar_y - 5), 
    #             cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # ESP32 connection status
    conn_color = (0, 255, 0) if esp32_connected else (0, 0, 255)
    conn_text = "ESP32: Connected" if esp32_connected else "ESP32: Disconnected"
    cv2.putText(frame, conn_text, (10, h - 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, conn_color, 2)
    
    return frame


def main():
    """Main tracking loop with WiFi servo control and audio alerts"""
    
    print("=" * 70)
    print("Hat Detection System - WiFi Servo Control + Audio Alerts")
    print("=" * 70)
    print(f"Model: {MODEL_PATH}")
    print(f"Camera: {CAMERA_SOURCE}")
    print(f"ESP32 URL: {ESP32_URL}")
    print(f"Alert Audio: {ALERT_AUDIO}")
    print(f"Servo Range: {SERVO_MIN}° - {SERVO_MAX}° (Home: {SERVO_HOME}°)")
    print(f"Dead Zone: ±{DEAD_ZONE_X}x, ±{DEAD_ZONE_Y}y pixels")
    print("=" * 70)
    
    # Load YOLO model
    print("\nLoading YOLO model...")
    model = YOLO(MODEL_PATH)
    print("✓ Model loaded")
    
    # Initialize ESP32 servo controller
    print(f"\nConnecting to ESP32 at {ESP32_IP}...")
    servo = ESP32ServoController(ESP32_URL, home_position=SERVO_HOME)
    if servo.test_connection():
        print("✓ ESP32 connected")
    else:
        print("⚠️  ESP32 not responding (will retry during operation)")
    
    # Initialize audio alert
    print("\nInitializing audio alert system...")
    audio_alert = AudioAlert(cooldown_seconds=ALERT_COOLDOWN)
    print("✓ Audio system ready")
    
    # Open camera
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        print("❌ Error: Cannot open camera")
        return
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Camera opened: {frame_width}x{frame_height}")
    
    print("\n" + "=" * 70)
    print("SERVO POSITION CONTROL")
    print("=" * 70)
    print("The servo will automatically track detected hats and return to")
    print(f"home position ({SERVO_HOME}°) when no hats are detected.")
    print("\nIMPORTANT: Make sure servo starts at center/home position!")
    print("Press 'r' during operation to reset servo to home")
    print("=" * 70)
    
    print("\n🎬 Starting hat tracking system...")
    print("Press 'q' to quit, 'r' to reset servo to home\n")
    
    # Initialize tracker
    tracker = HatTracker(frame_width, frame_height, servo_home=SERVO_HOME)
    
    servo.reset_to_home()
    time.sleep(1)  
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame_count += 1
            
            # Use tracking instead of prediction for consistent object IDs
            results = model.track(frame, conf=0.25, verbose=False, persist=True)
            
            # Get detected hats
            hats = tracker.get_detected_hats(results)
            
            if hats and ALERT_AUDIO:
                import os
                if os.path.exists(ALERT_AUDIO):
                    audio_alert.play_alert(ALERT_AUDIO, volume=0.8)
            
            target_hat = tracker.select_target_hat(hats)
            
            servo_command = None
            
            if target_hat:
                servo.cancel_return_home()
                
                servo_command = tracker.calculate_servo_position(
                    target_hat['center'],
                    servo.servo_position,
                    dead_zone_x=DEAD_ZONE_X
                )
                
                if servo_command['needs_adjustment']:
                    servo.move_to_position(servo_command['target_position'], step_size=SERVO_STEP)
                
                if frame_count % 30 == 0:
                    print(f"\n[Frame {frame_count}] Hats: {len(hats)} | " + 
                          f"Target: {target_hat['center']} | " +
                          f"Servo: {servo.servo_position}° → {servo_command['target_position']}° | " +
                          f"ESP32: {'✓' if servo.connected else '✗'}")
            else:
                is_returning = servo.return_to_home()
                
                wait_time = 0
                if servo.no_hat_start_time is not None:
                    elapsed = time.time() - servo.no_hat_start_time
                    wait_time = max(0, servo.return_home_delay - elapsed)
                
                if frame_count % 30 == 0:
                    if wait_time > 0:
                        print(f"\n[Frame {frame_count}] No hats - Waiting {wait_time:.1f}s before returning home")
                    elif is_returning:
                        print(f"\n[Frame {frame_count}] No hats detected - Returning to home | Servo: {servo.servo_position}°")
                    else:
                        print(f"\n[Frame {frame_count}] No hats detected - At home position ({servo.servo_position}°)")
            
            frame = draw_tracking_overlay(frame, hats, target_hat, servo_command, 
                                         servo.connected, servo.servo_position)
            
            cv2.imshow('Hat Tracking System - Servo Control', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                servo.reset_to_home()
                print("🔄 Servo manually reset to home")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  System stopped by user")
    finally:
        print("\nReturning servo to home position...")
        servo.reset_to_home()
        
        cap.release()
        cv2.destroyAllWindows()
        audio_alert.stop()
        print("✓ Cleanup complete")


if __name__ == "__main__":
    main()
