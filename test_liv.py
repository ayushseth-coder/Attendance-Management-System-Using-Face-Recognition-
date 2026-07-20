import cv2
import numpy as np
from models.anti_spoofing import liveness_detector

real_img = "real_face.jpg"
fake_img = "fake_print.jpg"

def test_image(img_path):
    print(f"\n--- Testing {img_path} ---")
    img = cv2.imread(img_path)
    if img is None:
        print("Image not found!")
        return

    # Haar Cascade logic to see bounding box
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        print("[Haar] No face detected.")
        return
        
    x, y, w, h = faces[0]
    print(f"[Haar] Face found: w={w}, img_width={img.shape[1]}, ratio={w/img.shape[1]:.2f}")
    
    # Run the exact liveness detector logic
    is_real, score = liveness_detector.check_liveness(img_path)
    print(f"[Result] is_real: {is_real}, score: {score}")

test_image(real_img)
test_image(fake_img)
