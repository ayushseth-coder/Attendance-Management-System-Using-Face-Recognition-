from models.database import db

def reset_system_data():
    collections_to_clear = [
        'visitor_log',
        'active_visitors',
        'request',
        'rejected_visitors',
        'status',
        'otp_store',
        'attendance_log',
        'other_logs'
    ]
    
    print("Starting system reset for testing...")
    
    for collection_name in collections_to_clear:
        result = db[collection_name].delete_many({})
        print(f"Cleared {result.deleted_count} records from '{collection_name}' collection.")
        
    print("System reset complete. All log and visitor data has been cleared.")
    print("Note: 'users' and 'universal_registry' (Employees) were kept safe.")

if __name__ == '__main__':
    reset_system_data()
