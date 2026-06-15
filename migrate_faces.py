import os
from deepface import DeepFace
from models.vector_db import employee_collection

def migrate_faces():
    # Path to the directory containing employee images
    faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee_faces')
    
    if not os.path.exists(faces_dir):
        print(f"[ERROR] Directory not found: {faces_dir}")
        return

    # Check if the collection is accessible
    if employee_collection is None:
        print("[ERROR] ChromaDB collection is not available. Please check vector_db.py.")
        return

    print(f"[INFO] Scanning directory: {faces_dir}")
    
    # Iterate through all files in the directory
    for filename in os.listdir(faces_dir):
        # Process only standard image formats
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(faces_dir, filename)
            
            # The employee's name is the filename without the extension
            employee_name = os.path.splitext(filename)[0]
            
            try:5
                print(f"[INFO] Extracting vector for: {employee_name}...")
                
                # Extract the 512-dimensional vector embedding
                # enforce_detection=False ensures it doesn't crash if lighting is bad
                # model_name="Facenet" is the optimized lightweight DeepFace model
                representations = DeepFace.represent(img_path=img_path, model_name="Facenet", enforce_detection=False)
                
                if representations and len(representations) > 0:
                    embedding = representations[0]["embedding"]
                    
                    # Insert into ChromaDB
                    employee_collection.upsert(
                        ids=[employee_name],            # Unique ID (Name)
                        embeddings=[embedding],         # The 512-d math vector
                        metadatas=[{"path": img_path}]  # Save the file path as metadata
                    )
                    print(f"[SUCCESS] Uploaded {employee_name} to ChromaDB!")
                else:
                    print(f"[WARNING] No face detected in {filename}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")

    print("\n[INFO] Migration Complete!")
    print(f"[INFO] Total vectors in database: {employee_collection.count()}")

if __name__ == "__main__":
    migrate_faces()
