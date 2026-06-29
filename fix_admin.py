from models.database import collection

collection.update_one({'Email': 'admin@admin.com'}, {'$set': {'Job': 'admin', 'Name': 'Initial Admin', 'Phone': '1234567890', 'address': 'N/A'}})
print("Fixed Admin!")
