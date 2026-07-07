from models.vector_db import employee_collection
from models.database import universal_registry

# Wipe ChromaDB employee collection
try:
    emp_res = employee_collection.get()
    if emp_res.get('ids'):
        employee_collection.delete(ids=emp_res['ids'])
        print(f"Deleted {len(emp_res['ids'])} from employee_collection")
    else:
        print("No employees found in collection to delete.")
except Exception as e:
    print(f"Error wiping chromadb: {e}")

# Note: We keep the Universal Registry and standard user MongoDB collection intact.
# This only wipes the biometric vectors to force re-enrollment with the new EMP-123 smart format.
