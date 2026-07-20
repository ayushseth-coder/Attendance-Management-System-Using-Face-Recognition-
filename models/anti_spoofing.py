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

            # Sort faces by size (largest first) so we don't accidentally check a background face
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces[0]
            
            # SECURITY FIX: MiniFASNet requires a 2.7x context window to see phone edges.
            # If the face is too large, the context window falls outside the camera frame,
            # and the model will falsely pass a fake image as real!
            # Max safe width is around 40-45% of the image.
            if w > img.shape[1] * 0.45:
                print(f"[WARNING] Face too close! (Width: {w}px). Context lost. Requesting step back.")
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
            input_data = resized_img.astype(np.float32) # Model expects 0-255 BGR raw pixels!
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
            
            is_real = real_score > 0.80
            
            # === DUAL-ENGINE: HEURISTIC CHECK ===
            try:
                gray_crop = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
                
                hsv_crop = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                sat_mean = hsv_crop[:,:,1].mean()
                
                print(f"[DEBUG] Anti-Spoof Heuristics -> Sharpness: {laplacian_var:.1f}, Saturation: {sat_mean:.1f}")
                
                # Balanced relaxed thresholds to allow real faces in average lighting
                is_heuristic_fake = False
                if laplacian_var < 60.0 or sat_mean < 20.0:
                    is_heuristic_fake = True
                
                if is_real and is_heuristic_fake:
                    print(f"[WARNING] Heuristic Engine VETOED AI Model! (Forced Fake). Score was {real_score:.3f}")
                    is_real = False
                    real_score = 0.0
            except Exception as e:
                print(f"[WARNING] Heuristic engine failed: {e}")
                
            return is_real, real_score

        except Exception as e:
            print(f"[ERROR] Liveness Check failed during inference: {e}")
            return True, 1.0 # Fail-safe

liveness_detector = LivenessDetector()
