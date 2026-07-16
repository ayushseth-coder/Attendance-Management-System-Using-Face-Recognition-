import os
import cv2
import numpy as np

class LivenessDetector:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'weights', 'MiniFASNetV2.onnx')
        self.session = None
        self.enabled = False
        
        try:
            import onnxruntime
            if os.path.exists(self.model_path):
                options = onnxruntime.SessionOptions()
                options.log_severity_level = 3
                self.session = onnxruntime.InferenceSession(self.model_path, options)
                self.enabled = True
                print("[INFO] Anti-Spoofing ONNX Model Loaded Successfully.")
            else:
                print(f"[WARNING] Anti-Spoofing ONNX model not found at {self.model_path}. Liveness check will be bypassed.")
        except ImportError:
            print("[WARNING] onnxruntime not installed. Liveness check bypassed.")
        except Exception as e:
            print(f"[ERROR] Failed to load Liveness model: {e}")

    def check_liveness(self, img_path):
        """
        Returns:
            is_real (bool): True if Real or if model bypassed, False if Spoof.
            score (float): Confidence score (0.0 to 1.0).
        """
        if not self.enabled:
            return True, 1.0  # Bypass if model is not set up

        try:
            img = cv2.imread(img_path)
            if img is None:
                return False, 0.0

            # MiniFASNet expects a wider context around the face (scale ~2.7x)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) == 0:
                print("[WARNING] No face detected by Haar Cascade. Cannot perform liveness check.")
                return "TooClose", 0.0

            x, y, w, h = faces[0]
            
            # SECURITY FIX: If the face is too close (takes up > 60% of camera width), 
            # the model cannot see the phone's edges and might falsely pass it as real.
            if w > img.shape[1] * 0.60:
                print(f"[WARNING] Face too close! (Width: {w}px). Requesting step back.")
                return "TooClose", 0.0
                
            cx, cy = x + w / 2, y + h / 2
            scale = 2.7
            new_w, new_h = w * scale, h * scale
            
            x1 = max(0, int(cx - new_w / 2))
            y1 = max(0, int(cy - new_h / 2))
            x2 = min(img.shape[1], int(cx + new_w / 2))
            y2 = min(img.shape[0], int(cy + new_h / 2))
            img = img[y1:y2, x1:x2]

            input_name = self.session.get_inputs()[0].name
            input_shape = self.session.get_inputs()[0].shape
            
            height, width = input_shape[2], input_shape[3]
            
            resized_img = cv2.resize(img, (width, height))
            resized_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
            input_data = resized_img.astype(np.float32) / 255.0
            input_data = np.transpose(input_data, (2, 0, 1)) # HWC to CHW
            input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension

            output_name = self.session.get_outputs()[0].name
            result = self.session.run([output_name], {input_name: input_data})[0]

            exp_res = np.exp(result[0])
            probs = exp_res / np.sum(exp_res)
            
            if len(probs) == 3:
                real_score = float(probs[1]) # Class 0: Print, Class 1: Real Face, Class 2: Replay
            elif len(probs) == 2:
                real_score = float(probs[1])
            else:
                real_score = float(probs[0])
            
            is_real = real_score > 0.50
            return is_real, real_score

        except Exception as e:
            print(f"[ERROR] Liveness Check failed during inference: {e}")
            return True, 1.0 # Fail-safe

liveness_detector = LivenessDetector()
