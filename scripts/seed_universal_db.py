import sys
import os
from datetime import datetime, timedelta
import random
from faker import Faker

# Add the parent directory to sys.path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.universal_db_helper import log_to_universal_registry
from models.database import universal_registry

fake = Faker()

def generate_mock_data(num_records=100):
    roles = ['Employee', 'Visitor', 'External Staff']
    
    print(f"Starting seeding of {num_records} records into universal_registry...")
    
    for i in range(num_records):
        role = random.choice(roles)
        raw_name = fake.name()
        
        # Generate random entry time in the past 30 days
        days_ago = random.randint(0, 30)
        entry_time_dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(1, 10))
        entry_time_str = entry_time_dt.strftime('%H:%M:%S')
        
        # 50% chance they checked out
        if random.random() > 0.5:
            exit_time_dt = entry_time_dt + timedelta(hours=random.randint(1, 8))
            exit_time_str = exit_time_dt.strftime('%H:%M:%S')
        else:
            exit_time_str = None
            
        # Give visitors an ID, others use their name
        visitor_id = str(random.randint(100000, 999999)) if role != 'Employee' else None
        
        log_to_universal_registry(
            raw_name=raw_name,
            role=role,
            entry_time_str=entry_time_str,
            exit_time_str=exit_time_str,
            visitor_id=visitor_id
        )
        
        if (i+1) % 50 == 0:
            print(f"Inserted {i+1}/{num_records} records...")

    print("Seeding complete!")
    print(f"Total records in Universal DB: {universal_registry.count_documents({})}")

if __name__ == "__main__":
    # Seed 150 users for testing
    generate_mock_data(150)
