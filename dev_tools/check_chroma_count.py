import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.vector_db import employee_collection, visitor_collection, other_collection

print("========================================")
print("   CHROMADB VECTOR DATABASE STATUS")
print("========================================")
print(f"1. employee_faces : {employee_collection.count()} registered vectors")
print(f"2. visitor_faces  : {visitor_collection.count()} registered vectors")
print(f"3. other_faces    : {other_collection.count()} registered vectors")
print("========================================")
