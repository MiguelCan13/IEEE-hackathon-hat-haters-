from ultralytics import YOLO
import numpy

#model = YOLO('yolo11n.pt')

'''
The following code is for training and validating a YOLO model for hat detection.
'''
#model = YOLO("..\\runs\\detect\\train_with_5000_hats\\weights\\best.pt")
#results = model.train(data="ultralytics_ai\\hats_only\\data.yaml", epochs=30, imgsz=640, save=True, name = "train_with_5000_hats_v2", device = "cpu")

#metrics = model.val()


# Optimized settings to reduce lag:
# - vid_stride=2: Process every 2nd frame (reduces CPU load)
# - Lower imgsz if still laggy
# - Try /stream without :81 if connection fails
'''
The below code is for real-time detection using the webcam or an ESP32-CAM stream.
'''
model = YOLO("..\\runs\\detect\\train_with_5000_hats_v2\\weights\\best.pt")


results_generator = model.track(
    source=0,  # "http://172.16.159.248:81/stream" for ESP32-CAM
    conf=0.25, 
    show=True, 
    tracker="bytetrack.yaml",
    vid_stride=2,  # Skip every other frame to reduce lag
    stream=True    # Stream=True returns a generator - must iterate through it
)

print("Starting camera... Press 'q' in the video window to quit")
for result in results_generator:
    
    pass

