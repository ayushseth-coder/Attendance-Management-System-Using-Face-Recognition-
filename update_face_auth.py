import re

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\face_auth.py', 'r') as f:
    content = f.read()

# Employee Exit
content = content.replace(
    '                                face_match_data["ExitTime"] = time_str',
    '                                face_match_data["ExitTime"] = time_str\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(employee_name, "Employee", existing_log.get("Date").split(" ")[1], time_str)'
)

# Employee Entry
content = content.replace(
    '                                attendance_log.insert_one(face_match_data)',
    '                                attendance_log.insert_one(face_match_data)\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(employee_name, "Employee", time_str, None)',
    1 # Only the first occurrence (Employee)
)

# Visitor Exit
content = content.replace(
    '                                face_match_data = existing_log\n' +
    '                                face_match_data["ExitTime"] = time_str',
    '                                face_match_data = existing_log\n' +
    '                                face_match_data["ExitTime"] = time_str\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(visitor_name, "Visitor", existing_log.get("Date").split(" ")[1], time_str)'
)

# Visitor Entry
content = content.replace(
    '                                    "ExitTime": None\n' +
    '                                }\n' +
    '                                attendance_log.insert_one(face_match_data)',
    '                                    "ExitTime": None\n' +
    '                                }\n' +
    '                                attendance_log.insert_one(face_match_data)\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(visitor_name, "Visitor", time_str, None)'
)

# External Exit
content = content.replace(
    '                                face_match_data = existing_log\n' +
    '                                face_match_data["ExitTime"] = time_str',
    '                                face_match_data = existing_log\n' +
    '                                face_match_data["ExitTime"] = time_str\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(external_name, role, existing_log.get("Date").split(" ")[1], time_str)'
)

# External Entry
content = content.replace(
    '                                    "ExitTime": None\n' +
    '                                }\n' +
    '                                attendance_log.insert_one(face_match_data)',
    '                                    "ExitTime": None\n' +
    '                                }\n' +
    '                                attendance_log.insert_one(face_match_data)\n' +
    '                                # SHADOW DB INJECTION\n' +
    '                                from models.universal_db_helper import log_to_universal_registry\n' +
    '                                log_to_universal_registry(external_name, role, time_str, None)'
)

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\face_auth.py', 'w') as f:
    f.write(content)

print("face_auth.py updated with Shadow DB hooks!")
