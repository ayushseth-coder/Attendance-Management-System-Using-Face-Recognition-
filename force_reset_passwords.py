from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

admin_pass = bcrypt.generate_password_hash('admin123').decode('utf-8')
collection.update_one({'Email': 'admin@admin.com'}, {'$set': {'Password': admin_pass, 'Job': 'admin'}}, upsert=True)

security_pass = bcrypt.generate_password_hash('security123').decode('utf-8')
collection.update_one({'Email': 'security@security.com'}, {'$set': {'Password': security_pass, 'Job': 'security'}}, upsert=True)

print("Passwords forcefully reset to admin123 and security123 (bcrypt hashes)")
