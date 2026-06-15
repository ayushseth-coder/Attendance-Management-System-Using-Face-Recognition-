from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['visitor_management']
collection = db['users']

collection.update_one({'Email': 'security@security.com'}, {'$set': {'Job': 'security'}})
print("Updated Job to 'security' for security@security.com")
