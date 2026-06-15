from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

collection.update_one({'Email': 'security@security.com'}, {'$set': {'Password': generate_password_hash('password123')}})
print("Password for security@security.com reset to: password123")
