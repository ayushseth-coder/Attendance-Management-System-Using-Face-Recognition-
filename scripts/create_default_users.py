import os
from flask import Flask
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from config.setting import MONGO_URI

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient(MONGO_URI)
db = client['visitor_management']
collection = db['users']

# 1. Create Default Admin User
if not collection.find_one({'Email': 'admin@admin.com'}):
    admin_pass = bcrypt.generate_password_hash('admin123').decode('utf-8')
    collection.insert_one({'Name': 'Admin', 'Email': 'admin@admin.com', 'Password': admin_pass, 'Job': 'admin'})
    print("[SUCCESS] Admin user created (admin@admin.com / admin123)")
else:
    print("[INFO] Admin user already exists in MongoDB Cloud")

# 2. Create Default Security User
if not collection.find_one({'Email': 'security@security.com'}):
    security_pass = bcrypt.generate_password_hash('security123').decode('utf-8')
    collection.insert_one({'Name': 'Security', 'Email': 'security@security.com', 'Password': security_pass, 'Job': 'security'})
    print("[SUCCESS] Security user created (security@security.com / security123)")
else:
    print("[INFO] Security user already exists in MongoDB Cloud")
