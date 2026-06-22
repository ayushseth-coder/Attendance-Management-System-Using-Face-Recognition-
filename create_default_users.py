from flask import Flask
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

app = Flask(__name__)
bcrypt = Bcrypt(app)
client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

if not collection.find_one({'Email': 'admin@admin.com'}):
    admin_pass = bcrypt.generate_password_hash('admin123').decode('utf-8')
    collection.insert_one({'Name': 'Admin', 'Email': 'admin@admin.com', 'Password': admin_pass, 'Job': 'admin'})
    print("Admin user created (admin@admin.com / admin123)")
else:
    print("Admin user already exists")

if not collection.find_one({'Email': 'security@security.com'}):
    security_pass = bcrypt.generate_password_hash('security123').decode('utf-8')
    collection.insert_one({'Name': 'Security', 'Email': 'security@security.com', 'Password': security_pass, 'Job': 'security'})
    print("Security user created (security@security.com / security123)")
else:
    print("Security user already exists")
