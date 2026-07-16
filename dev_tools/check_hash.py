from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

user = collection.find_one({'Email': 'security@security.com'})
if user:
    db_pass = user.get('Password')
    print(f"DB Hash: {db_pass}")
    from werkzeug.security import check_password_hash as werkzeug_check
    is_valid_password = werkzeug_check(db_pass, 'security123')
    if not is_valid_password and db_pass.startswith('$2b$'):
        is_valid_password = bcrypt.check_password_hash(db_pass, 'security123')
    print(f"Final is_valid_password: {is_valid_password}")
else:
    print("User not found in DB")
