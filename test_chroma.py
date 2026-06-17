import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.vector_db import chroma_client

try:
    print("Deleting old 128-dimensional collections...")
    chroma_client.delete_collection(name="employee_faces")
    print("Deleted employee_faces")
except Exception as e:
    print("Error deleting employee_faces:", e)

try:
    chroma_client.delete_collection(name="visitor_faces")
    print("Deleted visitor_faces")
except Exception as e:
    print("Error deleting visitor_faces:", e)

try:
    chroma_client.delete_collection(name="other_faces")
    print("Deleted other_faces")
except Exception as e:
    print("Error deleting other_faces:", e)

print("All old collections deleted. When you restart the Flask server, they will be recreated with the correct 512 dimensions for ArcFace!")
