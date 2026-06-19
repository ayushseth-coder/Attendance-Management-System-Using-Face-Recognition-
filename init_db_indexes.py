import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.database import collection, reqvistable, attendance_log

print("[INFO] Starting Database Indexing Process...")

# 1. Index 'Email' in the users collection (fast lookups for login & OTP)
try:
    collection.create_index("Email", unique=True)
    print("[SUCCESS] Created unique index on 'Email' in 'users' collection.")
except Exception as e:
    print(f"[ERROR] Failed to create index on 'Email': {e}")

# 2. Index 'UID' in reqvistable (fast lookups for visitors)
try:
    reqvistable.create_index("UID")
    print("[SUCCESS] Created index on 'UID' in 'reqvistable' collection.")
except Exception as e:
    print(f"[ERROR] Failed to create index on 'UID': {e}")

# 3. Index 'Name' and 'Date' in attendance_log (fast searching for records)
try:
    attendance_log.create_index("Name")
    attendance_log.create_index("Date")
    print("[SUCCESS] Created indexes on 'Name' and 'Date' in 'attendance_log' collection.")
except Exception as e:
    print(f"[ERROR] Failed to create indexes on 'attendance_log': {e}")

print("[INFO] Database Indexing Complete. MongoDB queries will now be significantly faster!")
