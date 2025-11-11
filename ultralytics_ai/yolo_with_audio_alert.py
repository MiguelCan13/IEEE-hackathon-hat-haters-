"""
YOLO Detection with Audio Alert System
Plays an MP3 alert on Bluetooth speaker when hats are detected
"""

from ultralytics import YOLO
import numpy as np
from audio_alert import AudioAlert
import os

# Configuration
MODEL_PATH = "..\\runs\\detect\\train_with_5000_hats\\weights\\best.pt"
ESP32_STREAM = "http://172.16.159.248:81/stream"  # "http://172.16.159.248:81/stream"
ALERT_AUDIO = "ultralytics_ai\\alert.mp3"  # Replace with your MP3 file path

# Detection thresholds
CONFIDENCE_THRESHOLD = 0.4
MIN_DETECTIONS = 1  # Minimum number of hats to trigger alert

# Initialize audio alert system (5 second cooldown between alerts)
audio_alert = AudioAlert(cooldown_seconds=5)

def check_detection_conditions(results):
    """
    Check if detection conditions are met to trigger alert.
    
    Parameters:
    -----------
    results : YOLO results object
        Detection results from YOLO model
    
    Returns:
    --------
    tuple : (bool, dict) - (condition_met, detection_info)
    """
    
    if len(results) == 0 or results[0].boxes is None:
        return False, {}
    
    boxes = results[0].boxes
    
    # Count detections above confidence threshold
    high_conf_detections = []
    for box in boxes:
        conf = float(box.conf[0])
        if conf >= CONFIDENCE_THRESHOLD:
            high_conf_detections.append({
                'confidence': conf,
                'class': int(box.cls[0]),
                'bbox': box.xyxy[0].tolist()
            })
    
    detection_count = len(high_conf_detections)
    
    # Check if conditions are met
    condition_met = detection_count >= MIN_DETECTIONS
    
    detection_info = {
        'count': detection_count,
        'detections': high_conf_detections,
        'max_confidence': max([d['confidence'] for d in high_conf_detections]) if high_conf_detections else 0
    }
    
    return condition_met, detection_info


def run_detection_with_alerts():
    """
    Run YOLO detection on ESP32-CAM stream and play audio alerts when conditions are met.
    """
    
    print("=" * 60)
    print("YOLO Detection with Audio Alert System")
    print("=" * 60)
    print(f"Model: {MODEL_PATH}")
    print(f"Stream: {ESP32_STREAM}")
    print(f"Alert Audio: {ALERT_AUDIO}")
    print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Min Detections for Alert: {MIN_DETECTIONS}")
    print("=" * 60)
    
    # Check if audio file exists
    if not os.path.exists(ALERT_AUDIO):
        print(f"⚠️  Warning: Audio file '{ALERT_AUDIO}' not found!")
        print("Alert sounds will not play. Please add an MP3 file.")
    
    # Load YOLO model
    print("\nLoading YOLO model...")
    model = YOLO(MODEL_PATH)
    print("✓ Model loaded successfully")
    
    # Start tracking
    print(f"\n🎥 Starting detection from {ESP32_STREAM}...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Process stream
        results_generator = model.track(
            source=ESP32_STREAM,
            conf=0.25,
            show=True,
            tracker="bytetrack.yaml",
            vid_stride=2,
            verbose=False,
            stream=True  # Important: return generator for frame-by-frame processing
        )
        
        frame_count = 0
        
        for results in results_generator:
            frame_count += 1
            
            # Check if detection conditions are met
            condition_met, detection_info = check_detection_conditions([results])
            
            if condition_met:
                count = detection_info['count']
                max_conf = detection_info['max_confidence']
                
                print(f"[Frame {frame_count}] 🎯 Detected {count} hat(s) - Max confidence: {max_conf:.2f}")
                
                # Play alert
                if os.path.exists(ALERT_AUDIO):
                    audio_alert.play_alert(ALERT_AUDIO, volume=0.8)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Detection stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        audio_alert.stop()
        print("✓ Cleanup complete")


if __name__ == "__main__":
    run_detection_with_alerts()
