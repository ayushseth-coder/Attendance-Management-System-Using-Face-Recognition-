from models.database import universal_registry
import json

def print_universal_db():
    print("\n" + "="*50)
    print(" LIVE UNIVERSAL DATABASE SCAN ")
    print("="*50 + "\n")
    
    # Fetch all records
    records = list(universal_registry.find())
    
    if not records:
        print(" The Universal Database is currently empty.")
        print("Try scanning a face or enrolling an employee to see it in action!")
        return
        
    print(f"Total Records Found: {len(records)}\n")
    
    for record in records:
        print(f" ID: {record.get('_id')}")
        print(f" Name: {record.get('Name')}")
        print(f" Role: {record.get('Role')}")
        print(f"  Type: {record.get('Visitor_Type')}")
        
        # Print attendance history neatly
        logs = record.get('Attendance_Logs', [])
        print(f" Attendance History ({len(logs)} entries):")
        if not logs:
            print("   - No scans yet.")
        else:
            for idx, log in enumerate(logs):
                print(f"   [{idx+1}] Date: {log.get('Date')} | In: {log.get('In_Time')} | Out: {log.get('Out_Time')}")
        print("-" * 40)

if __name__ == "__main__":
    print_universal_db()
