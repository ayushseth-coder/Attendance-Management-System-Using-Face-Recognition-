from models.vector_db import visitor_collection, other_collection
from models.database import universal_registry

# Wipe ChromaDB collections
try:
    vis_res = visitor_collection.get()
    if vis_res.get('ids'):
        visitor_collection.delete(ids=vis_res['ids'])
        print(f"Deleted {len(vis_res['ids'])} from visitor_collection")

    oth_res = other_collection.get()
    if oth_res.get('ids'):
        other_collection.delete(ids=oth_res['ids'])
        print(f"Deleted {len(oth_res['ids'])} from other_collection")
except Exception as e:
    print(f"Error wiping chromadb: {e}")

# Wipe Universal Registry where Role != Employee
try:
    res = universal_registry.delete_many({"Role": {"$ne": "Employee"}})
    print(f"Deleted {res.deleted_count} non-employee profiles from universal_registry")
except Exception as e:
    print(f"Error wiping universal registry: {e}")
