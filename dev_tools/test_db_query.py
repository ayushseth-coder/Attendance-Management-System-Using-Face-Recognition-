import os
import sys
from deepface import DeepFace

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.vector_db import employee_collection

base_dir = os.path.dirname(os.path.abspath(__file__))
# Find the latest shot
shots_dir = os.path.join(base_dir, 'static', 'shots')
latest_shot = sorted([f for f in os.listdir(shots_dir) if f.endswith('.png')])[-1]
img_path = os.path.join(shots_dir, latest_shot)

print(f"Testing latest shot: {latest_shot}")

try:
    representations = DeepFace.represent(img_path=img_path, model_name="ArcFace", enforce_detection=False)
    if representations:
        embedding = representations[0]["embedding"]
        results = employee_collection.query(
            query_embeddings=[embedding],
            n_results=1
        )
        print(f"Query Results: {results}")
        if results['ids'] and len(results['ids'][0]) > 0:
            distance = results['distances'][0][0]
            name = results['ids'][0][0]
            print(f"Match: {name}")
            print(f"Distance: {distance}")
            print(f"Is Distance < 0.68 ? {distance < 0.68}")
except Exception as e:
    print(f"Error: {e}")
