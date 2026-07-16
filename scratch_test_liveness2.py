import sys
import os
import cv2
import numpy as np

# Load ONNX model
model_path = 'models/weights/MiniFASNetV2.onnx'
import onnxruntime
session = onnxruntime.InferenceSession(model_path)
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape
height, width = input_shape[2], input_shape[3]
print(f"Model expects input: {width}x{height}")

# Test with a dummy black image
img = np.zeros((480, 640, 3), dtype=np.uint8)

# Try processing the whole image (no crop)
resized_img = cv2.resize(img, (width, height))
input_data = resized_img.astype(np.float32) / 255.0
input_data = np.transpose(input_data, (2, 0, 1)) # HWC to CHW
input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension

output_name = session.get_outputs()[0].name
result = session.run([output_name], {input_name: input_data})[0]
exp_res = np.exp(result[0])
probs = exp_res / np.sum(exp_res)
print(f"Dummy Image Output probs: {probs}")

# Now let's try with an actual captured face from the project if available
# We can check static/shots/
import glob
shots = glob.glob('static/shots/*.png')
if shots:
    test_img_path = shots[0]
    print(f"Testing on {test_img_path}")
    test_img = cv2.imread(test_img_path)
    
    # 1. Full image
    resized = cv2.resize(test_img, (width, height))
    inp = resized.astype(np.float32) / 255.0
    inp = np.transpose(inp, (2, 0, 1))
    inp = np.expand_dims(inp, axis=0)
    res = session.run([output_name], {input_name: inp})[0]
    exp_res = np.exp(res[0])
    probs_full = exp_res / np.sum(exp_res)
    print(f"Full Image probs: {probs_full}")
    
    # 2. Tight Crop (what we currently do)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) > 0:
        x, y, w, h = faces[0]
        crop = test_img[y:y+h, x:x+w]
        resized = cv2.resize(crop, (width, height))
        inp = resized.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))
        inp = np.expand_dims(inp, axis=0)
        res = session.run([output_name], {input_name: inp})[0]
        exp_res = np.exp(res[0])
        probs_crop = exp_res / np.sum(exp_res)
        print(f"Tight Crop probs: {probs_crop}")
        
    # 3. Wide Crop (scale 2.7x) - common for MiniFASNet
    if len(faces) > 0:
        scale = 2.7
        x, y, w, h = faces[0]
        center_x = x + w/2
        center_y = y + h/2
        new_w = w * scale
        new_h = h * scale
        x1 = max(0, int(center_x - new_w/2))
        y1 = max(0, int(center_y - new_h/2))
        x2 = min(test_img.shape[1], int(center_x + new_w/2))
        y2 = min(test_img.shape[0], int(center_y + new_h/2))
        crop_wide = test_img[y1:y2, x1:x2]
        resized = cv2.resize(crop_wide, (width, height))
        inp = resized.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))
        inp = np.expand_dims(inp, axis=0)
        res = session.run([output_name], {input_name: inp})[0]
        exp_res = np.exp(res[0])
        probs_wide = exp_res / np.sum(exp_res)
        print(f"Wide Crop 2.7x probs: {probs_wide}")
else:
    print("No shots found to test.")
