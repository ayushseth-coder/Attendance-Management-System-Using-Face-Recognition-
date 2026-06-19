import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.database import collection

users = collection.find({})
print("Current Users in DB:")
for u in users:
    print(f"Name: {u.get('Name')}, Email: {u.get('Email')}, Role: {u.get('Job')}")
