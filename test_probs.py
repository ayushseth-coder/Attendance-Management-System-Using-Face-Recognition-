import cv2
import numpy as np
from models.anti_spoofing import liveness_detector

real_img = "real_face.jpg"
fake_img = "fake_print.jpg"

def test_raw_probs(img_path):
    print(f"\n--- Testing raw probs for {img_path} ---")
    img = cv2.imread(img_path)
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    x, y, w, h = faces[0]
    
    cx, cy = x + w / 2, y + h / 2
    scale = 2.7
    new_w, new_h = w * scale, h * scale
    
    x1 = max(0, int(cx - new_w / 2))
    y1 = max(0, int(cy - new_h / 2))
    x2 = min(img.shape[1], int(cx + new_w / 2))
    y2 = min(img.shape[0], int(cy + new_h / 2))
    img = img[y1:y2, x1:x2]

    input_name = liveness_detector.session.get_inputs()[0].name
    input_shape = liveness_detector.session.get_inputs()[0].shape
    height, width = input_shape[2], input_shape[3]
    
    resized_img = cv2.resize(img, (width, height))
    
    # Test 1: BGR, 0-255
    inp1 = np.expand_dims(np.transpose(resized_img.astype(np.float32), (2, 0, 1)), axis=0)
    res1 = liveness_detector.session.run(None, {input_name: inp1})[0]
    
    # Test 2: RGB, 0-255
    inp2 = np.expand_dims(np.transpose(cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB).astype(np.float32), (2, 0, 1)), axis=0)
    res2 = liveness_detector.session.run(None, {input_name: inp2})[0]
    
    # Test 3: BGR, 0-1
    inp3 = np.expand_dims(np.transpose((resized_img.astype(np.float32)/255.0), (2, 0, 1)), axis=0)
    res3 = liveness_detector.session.run(None, {input_name: inp3})[0]
    
    # Test 4: RGB, 0-1
    inp4 = np.expand_dims(np.transpose((cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB).astype(np.float32)/255.0), (2, 0, 1)), axis=0)
    res4 = liveness_detector.session.run(None, {input_name: inp4})[0]
    
    def softmax(x):
        e = np.exp(x)
        return e / np.sum(e)
        
    print(f"Test 1 (BGR, 0-255): {softmax(res1[0])}")
    print(f"Test 2 (RGB, 0-255): {softmax(res2[0])}")
    print(f"Test 3 (BGR, 0-1): {softmax(res3[0])}")
    print(f"Test 4 (RGB, 0-1): {softmax(res4[0])}")

test_raw_probs(real_img)
test_raw_probs(fake_img)
