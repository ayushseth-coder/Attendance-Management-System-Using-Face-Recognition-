import urllib.request
import cv2
import numpy as np
import onnxruntime

# Download a real face and a fake face (just arbitrary images)
# For real face, let's use a standard test image (Lenna or similar, but let's use a clear face)
urllib.request.urlretrieve("https://raw.githubusercontent.com/minivision-ai/Silent-Face-Anti-Spoofing/master/images/sample/image_F1.jpg", "fake_print.jpg")
urllib.request.urlretrieve("https://raw.githubusercontent.com/minivision-ai/Silent-Face-Anti-Spoofing/master/images/sample/image_T1.jpg", "real_face.jpg")

model_path = 'models/weights/MiniFASNetV2.onnx'
session = onnxruntime.InferenceSession(model_path)
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape
height, width = input_shape[2], input_shape[3]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def test_img(path, name):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) > 0:
        x, y, w, h = faces[0]
        cx = x + w/2
        cy = y + h/2
        scale = 2.7
        new_w = w * scale
        new_h = h * scale
        x1 = max(0, int(cx - new_w/2))
        y1 = max(0, int(cy - new_h/2))
        x2 = min(img.shape[1], int(cx + new_w/2))
        y2 = min(img.shape[0], int(cy + new_h/2))
        crop = img[y1:y2, x1:x2]
        
        resized = cv2.resize(crop, (width, height))
        inp = resized.astype(np.float32) / 255.0
        # PyTorch ImageNet Normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        inp = (inp - mean) / std
        
        inp = np.transpose(inp, (2, 0, 1))
        inp = np.expand_dims(inp, axis=0)
        
        res = session.run([session.get_outputs()[0].name], {input_name: inp})[0]
        exp_res = np.exp(res[0])
        probs = exp_res / np.sum(exp_res)
        print(f"--- {name} ---")
        print(f"Probs: {probs}")
        print(f"Argmax: {np.argmax(probs)}")
    else:
        print(f"No face in {name}")

test_img("fake_print.jpg", "FAKE PRINT")
test_img("real_face.jpg", "REAL FACE")
