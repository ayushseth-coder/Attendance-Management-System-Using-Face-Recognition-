from models.database import db

def cleanup_duplicates():
    # Clean up visitors_status
    status_collection = db['status']
    pipeline = [
        {"$group": {"_id": "$UID", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = status_collection.aggregate(pipeline)
    for duplicate in duplicates:
        # Keep the first document, delete the rest
        docs_to_delete = duplicate['docs'][1:]
        status_collection.delete_many({"_id": {"$in": docs_to_delete}})
        print(f"Removed duplicate from visitors_status for UID: {duplicate['_id']}")

    # Clean up reqvistable
    req_collection = db['request']
    req_duplicates = req_collection.aggregate(pipeline)
    for duplicate in req_duplicates:
        docs_to_delete = duplicate['docs'][1:]
        req_collection.delete_many({"_id": {"$in": docs_to_delete}})
        print(f"Removed duplicate from request table for UID: {duplicate['_id']}")
        
    print("Cleanup complete.")

if __name__ == '__main__':
    cleanup_duplicates()
