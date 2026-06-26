import datetime
import random
import re
from models.database import universal_registry

def generate_smart_id(role, name_or_phone):
    """Generates the Smart Prefix ID based on the Role."""
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    if role.lower() == 'employee':
        # Fallback if no numbers in name
        return f"EMP-{name_or_phone.upper()}"
    elif 'visitor' in role.lower():
        random_suffix = random.randint(1000, 9999)
        return f"VIS-{date_str}-{random_suffix}"
    else:
        random_suffix = random.randint(1000, 9999)
        return f"OTH-{date_str}-{random_suffix}"

def log_to_universal_registry(raw_name, role, entry_time_str, exit_time_str=None, visitor_id=None):
    """
    Safely injects or updates a person in the Universal Registry.
    Wrapped in try/except to guarantee it never breaks the old architecture.
    """
    try:
        visitor_type = "Regular" if role.lower() == 'employee' else "One-Time"
        
        if role.lower() == 'employee':
            match = re.match(r"([A-Za-z]+)(\d*)", raw_name)
            if match:
                clean_name = match.group(1).capitalize()
                extracted_id = match.group(2) if match.group(2) else None
            else:
                clean_name = raw_name.capitalize()
                extracted_id = None
                
            smart_id = f"EMP-{extracted_id}" if extracted_id else f"EMP-{clean_name.upper()}"
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # The State vs Ledger Architecture: OVERWRITE the current state for registered employees!
            universal_registry.update_one(
                {"_id": smart_id},
                {
                    "$set": {
                        "Date": today_str,
                        "In_Time": entry_time_str,
                        "Out_Time": exit_time_str
                    },
                    "$setOnInsert": {
                        "Name": clean_name,
                        "Role": role,
                        "Phone": "Unknown",
                        "Email": "Unknown",
                        "Address": "Unknown",
                        "Leave_Status": "Active",
                        "Visitor_Type": visitor_type
                    }
                },
                upsert=True
            )
                
        else:
            # One-Time Visitors & External Staff
            # If they are a Regular Visitor or External Staff (their name is known), use a permanent ID!
            if raw_name.lower() not in ["unknown visitor", "unknown"]:
                prefix = "REGVIS" if 'visitor' in role.lower() else "EXTSTF"
                if visitor_id:
                    smart_id = f"{prefix}-{visitor_id}"
                else:
                    clean_name = raw_name.replace(" ", "").upper()
                    smart_id = f"{prefix}-{clean_name}"
                
                # OVERWRITE state for known regular visitors
                today_str = datetime.datetime.now().strftime('%Y-%m-%d')
                universal_registry.update_one(
                    {"_id": smart_id},
                    {
                        "$set": {
                            "Date": today_str,
                            "In_Time": entry_time_str,
                            "Out_Time": exit_time_str
                        },
                        "$setOnInsert": {
                            "Name": raw_name,
                            "Role": role,
                            "Phone": "Unknown",
                            "Email": "Unknown",
                            "Address": "Unknown",
                            "Visitor_Type": "Regular"
                        }
                    },
                    upsert=True
                )
            else:
                # Truly unknown, random one-time visitor
                smart_id = generate_smart_id(role, raw_name)
                today_str = datetime.datetime.now().strftime('%Y-%m-%d')
                
                new_profile = {
                    "_id": smart_id,
                    "Name": raw_name,
                    "Role": role,
                    "Phone": "Unknown",
                    "Email": "Unknown",
                    "Address": "Unknown",
                    "Visitor_Type": visitor_type,
                    "Date": today_str,
                    "In_Time": entry_time_str,
                    "Out_Time": exit_time_str
                }
                universal_registry.insert_one(new_profile)
            
    except Exception as e:
        print(f"[SHADOW DB ERROR] Failed to log to Universal Registry: {e}")
