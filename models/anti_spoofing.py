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

            input_name = self.session.get_inputs()[0].name
            input_shape = self.session.get_inputs()[0].shape
            
            height, width = input_shape[2], input_shape[3]
            
            resized_img = cv2.resize(img, (width, height))
            input_data = resized_img.astype(np.float32) / 255.0
            input_data = np.transpose(input_data, (2, 0, 1)) # HWC to CHW
            input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension

            output_name = self.session.get_outputs()[0].name
            result = self.session.run([output_name], {input_name: input_data})[0]

            exp_res = np.exp(result[0])
            probs = exp_res / np.sum(exp_res)
            
            real_score = float(probs[1]) if len(probs) > 1 else float(probs[0])
            
            is_real = real_score > 0.85
            return is_real, real_score

        except Exception as e:
            print(f"[ERROR] Liveness Check failed during inference: {e}")
            return True, 1.0 # Fail-safe

liveness_detector = LivenessDetector()
