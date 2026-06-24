from models.database import collection
collection.update_one({'Email': 'admin@admin.com'}, {'$set': {'Job': 'Admin', 'Name': 'Admin'}})
print("Fixed Admin")
