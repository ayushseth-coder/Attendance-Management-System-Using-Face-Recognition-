from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

print("All Users:")
for u in collection.find():
    print(f"- Email: {u.get('Email')}, Job: {u.get('Job')}")
