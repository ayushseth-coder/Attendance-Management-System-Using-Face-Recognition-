import cv2
import numpy as np
import onnxruntime

model_path = 'models/weights/MiniFASNetV2.onnx'
session = onnxruntime.InferenceSession(model_path)
input_name = session.get_inputs()[0].name
height, width = session.get_inputs()[0].shape[2:]

def test(path):
    img = cv2.imread(path)
    # RAW BGR, no division by 255!
    resized = cv2.resize(img, (width, height))
    inp = resized.astype(np.float32)
    inp = np.transpose(inp, (2, 0, 1))
    inp = np.expand_dims(inp, axis=0)
    
    res = session.run([session.get_outputs()[0].name], {input_name: inp})[0]
    exp_res = np.exp(res[0])
    probs = exp_res / np.sum(exp_res)
    print(f"[{path}] Probs: {probs} | Argmax: {np.argmax(probs)}")

test("fake_print.jpg")
test("real_face.jpg")
