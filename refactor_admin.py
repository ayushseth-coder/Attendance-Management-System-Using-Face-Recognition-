import re

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'r') as f:
    content = f.read()

# 1. Update manage_visitors
target1 = """    try:
        results = visitor_collection.get()
        visitor_names = results.get('ids', [])
        total_count = len(visitor_names)
        
        visitor_profiles = []
        for name in visitor_names:
            clean_name = name.replace(" ", "").upper()
            smart_id = f"REGVIS-{clean_name}"
            profile = universal_registry.find_one({"_id": smart_id})
            if profile:
                visitor_profiles.append(profile)
            else:
                visitor_profiles.append({"Name": name, "Phone": "Unknown", "Email": "Unknown"})"""

replace1 = """    try:
        results = visitor_collection.get(include=["documents"])
        visitor_ids = results.get('ids', [])
        documents = results.get('documents', [])
        total_count = len(visitor_ids)
        
        visitor_profiles = []
        for i, vis_id in enumerate(visitor_ids):
            smart_id = f"REGVIS-{vis_id}"
            profile = universal_registry.find_one({"_id": smart_id})
            name = documents[i] if documents and i < len(documents) and documents[i] else vis_id
            
            if profile:
                profile['num_id'] = vis_id
                visitor_profiles.append(profile)
            else:
                visitor_profiles.append({"num_id": vis_id, "Name": name, "Phone": "Unknown", "Email": "Unknown"})"""

content = content.replace(target1, replace1)

# 2. Update update_visitor_details
target2 = """    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    
    if name:
        clean_name = name.replace(" ", "").upper()
        smart_id = f"REGVIS-{clean_name}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')"""

replace2 = """    visitor_id = request.form.get('visitor_id')
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    
    if visitor_id and name:
        smart_id = f"REGVIS-{visitor_id}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')"""

content = content.replace(target2, replace2)

# 3. Update delete_visitor
content = content.replace("@admin.route('/delete_visitor/<name>', methods=['POST'])\ndef delete_visitor(name):", "@admin.route('/delete_visitor/<visitor_id>', methods=['POST'])\ndef delete_visitor(visitor_id):")
content = content.replace("visitor_collection.delete(ids=[name])", "visitor_collection.delete(ids=[visitor_id])")
# To avoid replacing all flash messages:
content = content.replace('flash(f"Successfully deleted records for {name}.", "success")', 'flash(f"Successfully deleted records for ID {visitor_id}.", "success")')
content = content.replace('if name_without_ext.lower() == name.lower():', 'if name_without_ext.lower() == visitor_id.lower():')
content = content.replace('flash(f"Error deleting {name}: {e}", "danger")', 'flash(f"Error deleting {visitor_id}: {e}", "danger")')


# 4. Update manage_other
target4 = """    try:
        results = other_collection.get(include=["metadatas"])
        other_names = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        total_count = len(other_names)
        
        external_staff = []
        for i in range(total_count):
            name = other_names[i]
            role = metadatas[i].get('Role', 'Unknown') if metadatas and i < len(metadatas) and metadatas[i] else 'Unknown'
            
            clean_name = name.replace(" ", "").upper()
            smart_id = f"EXTSTF-{clean_name}"
            profile = universal_registry.find_one({"_id": smart_id})
            
            if profile:
                # Ensure the ChromaDB role is passed through if missing
                if "Role" not in profile or profile["Role"] == "Unknown":
                    profile["Role"] = role
                external_staff.append(profile)
            else:
                external_staff.append({"Name": name, "Role": role, "Phone": "Unknown", "Email": "Unknown"})"""

replace4 = """    try:
        results = other_collection.get(include=["metadatas", "documents"])
        other_ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        total_count = len(other_ids)
        
        external_staff = []
        for i, stf_id in enumerate(other_ids):
            name = documents[i] if documents and i < len(documents) and documents[i] else stf_id
            role = metadatas[i].get('Role', 'Unknown') if metadatas and i < len(metadatas) and metadatas[i] else 'Unknown'
            
            smart_id = f"EXTSTF-{stf_id}"
            profile = universal_registry.find_one({"_id": smart_id})
            
            if profile:
                profile['num_id'] = stf_id
                # Ensure the ChromaDB role is passed through if missing
                if "Role" not in profile or profile["Role"] == "Unknown":
                    profile["Role"] = role
                external_staff.append(profile)
            else:
                external_staff.append({"num_id": stf_id, "Name": name, "Role": role, "Phone": "Unknown", "Email": "Unknown"})"""

content = content.replace(target4, replace4)


# 5. Update update_other_details
target5 = """    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    role = request.form.get('role', 'Unknown')
    
    if name:
        clean_name = name.replace(" ", "").upper()
        smart_id = f"EXTSTF-{clean_name}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')"""

replace5 = """    staff_id = request.form.get('staff_id')
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    role = request.form.get('role', 'Unknown')
    
    if staff_id and name:
        smart_id = f"EXTSTF-{staff_id}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')"""

content = content.replace(target5, replace5)


# 6. Update delete_other
content = content.replace("@admin.route('/delete_other/<name>', methods=['POST'])\ndef delete_other(name):", "@admin.route('/delete_other/<staff_id>', methods=['POST'])\ndef delete_other(staff_id):")
content = content.replace("other_collection.delete(ids=[name])", "other_collection.delete(ids=[staff_id])")
# To avoid replacing all flash messages:
content = content.replace('flash(f"Successfully deleted records for {name}.", "success")', 'flash(f"Successfully deleted records for ID {staff_id}.", "success")')
# Wait, name_without_ext is compared to `name`
# content = content.replace('if name_without_ext.lower() == name.lower():', 'if name_without_ext.lower() == staff_id.lower():')
# I'll just regex replace it to be safe
content = re.sub(r'if name_without_ext\.lower\(\) == name\.lower\(\):', r'if name_without_ext.lower() == staff_id.lower():', content)
content = re.sub(r'flash\(f"Error deleting \{name\}: \{e\}", "danger"\)', r'flash(f"Error deleting {staff_id}: {e}", "danger")', content)


with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'w') as f:
    f.write(content)

print("admin.py updated")
