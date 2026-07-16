import os
from models.vector_db import employee_collection

def delete_employee(name):
    # Capitalize the name to match how it's stored in the database
    formatted_name = name.capitalize()
    
    try:
        # Delete the specific ID from the vector database
        employee_collection.delete(ids=[formatted_name])
        print(f"[SUCCESS] Successfully deleted '{formatted_name}' from the Face Database.")
    except Exception as e:
        print(f"[ERROR] Could not delete '{formatted_name}': {e}")

if __name__ == "__main__":
    print("=== ChromaDB Employee Deletion Utility ===")
    print("Type the name of the employee you want to delete (or type 'exit' to quit).")
    
    while True:
        name_to_delete = input("\nEmployee Name to delete: ")
        
        if name_to_delete.lower() == 'exit':
            break
            
        if name_to_delete.strip() == "":
            continue
            
        delete_employee(name_to_delete.strip())
