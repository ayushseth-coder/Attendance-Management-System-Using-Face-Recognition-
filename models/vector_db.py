import os
import chromadb
from chromadb.config import Settings

# Get the absolute path to the chroma_db directory in the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'chroma_db')

# Initialize the ChromaDB client with persistent local storage
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Create or get the collection for storing employee face vectors
    # We use cosine similarity (the standard for face recognition vectors)
    employee_collection = chroma_client.get_or_create_collection(
        name="employee_faces",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Create or get the collection for storing regular visitor face vectors
    visitor_collection = chroma_client.get_or_create_collection(
        name="visitor_faces",
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"[INFO] ChromaDB successfully initialized at {CHROMA_DB_PATH}")
    print(f"[INFO] Collection 'employee_faces' loaded. Total records: {employee_collection.count()}")
    print(f"[INFO] Collection 'visitor_faces' loaded. Total records: {visitor_collection.count()}")

except Exception as e:
    print(f"[ERROR] Failed to initialize ChromaDB: {e}")
    chroma_client = None
    employee_collection = None
    visitor_collection = None
