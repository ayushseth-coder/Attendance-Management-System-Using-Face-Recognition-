from models.vector_db import employee_collection

def list_all_employees():
    try:
        # The .get() method fetches all records if no IDs are specified
        results = employee_collection.get()
        
        employee_names = results.get('ids', [])
        total_count = len(employee_names)
        
        print("\n=== ChromaDB Employee Directory ===")
        print(f"Total Enrolled Employees: {total_count}")
        print("-" * 35)
        
        if total_count == 0:
            print("The database is currently empty.")
        else:
            for i, name in enumerate(employee_names, 1):
                print(f"{i}. {name}")
                
        print("===================================\n")
        
    except Exception as e:
        print(f"[ERROR] Could not fetch employees: {e}")

if __name__ == "__main__":
    list_all_employees()
