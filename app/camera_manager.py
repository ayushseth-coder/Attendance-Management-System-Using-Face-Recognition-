# app/camera_manager.py
import cv2

import time

camera = None
def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        if not camera.isOpened():
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        # Buffer Flush & Warm-up
        # Give the hardware sensors 0.5 seconds to turn on and adjust exposure
        time.sleep(0.5) 
        
        # Read and throw away the first 5 frames to clear OpenCV's hidden buffer of dark/stale images
        for _ in range(5):
            camera.read()
            
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        cv2.destroyAllWindows()
        camera = None
