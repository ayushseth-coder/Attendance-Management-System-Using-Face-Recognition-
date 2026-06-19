from deepface import DeepFace
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

img1 = os.path.join(base_dir, 'employee_faces', 'Test99.png')
img2 = os.path.join(base_dir, 'static', 'shots', 'shot_20260618_123854.png')

print(f"Testing ArcFace distance between {img1} and {img2}...")
try:
    result = DeepFace.verify(
        img1_path=img1, 
        img2_path=img2, 
        model_name="ArcFace", 
        distance_metric="cosine", 
        enforce_detection=False
    )
    print("ArcFace Result:")
    print(f"Verified: {result['verified']}")
    print(f"Distance: {result['distance']}")
    print(f"ArcFace Default Threshold: {result['threshold']}")
except Exception as e:
    print(f"Error: {e}")
