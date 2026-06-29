import re

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'r') as f:
    content = f.read()

# 1. Update manage_visitors
target1 = """@admin.route('/manage_visitors', methods=['GET'])
def manage_visitors():
    from models.vector_db import visitor_collection
    
    try:
        results = visitor_collection.get()
        visitor_names = results.get('ids', [])
        total_count = len(visitor_names)
    except Exception as e:
        print(f"[ERROR] Could not fetch visitors: {e}")
        visitor_names = []
        total_count = 0
        flash("Failed to load visitors from database.", "danger")
        
    return render_template('manage_visitors.html', visitor_names=visitor_names, total_count=total_count)"""

replace1 = """@admin.route('/manage_visitors', methods=['GET'])
def manage_visitors():
    from models.vector_db import visitor_collection
    from models.database import universal_registry
    
    try:
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
                visitor_profiles.append({"Name": name, "Phone": "Unknown", "Email": "Unknown"})
                
    except Exception as e:
        print(f"[ERROR] Could not fetch visitors: {e}")
        visitor_profiles = []
        total_count = 0
        flash("Failed to load visitors from database.", "danger")
        
    return render_template('manage_visitors.html', visitor_profiles=visitor_profiles, total_count=total_count)

@admin.route('/update_visitor_details', methods=['POST'])
def update_visitor_details():
    from models.database import universal_registry
    import datetime
    
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    
    if name:
        clean_name = name.replace(" ", "").upper()
        smart_id = f"REGVIS-{clean_name}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        universal_registry.update_one(
            {"_id": smart_id},
            {
                "$set": {
                    "Email": email,
                    "Phone": phone
                },
                "$setOnInsert": {
                    "Name": name,
                    "Role": "Visitor",
                    "Address": "Unknown",
                    "Visitor_Type": "Regular",
                    "Date": today_str,
                    "In_Time": None,
                    "Out_Time": None
                }
            },
            upsert=True
        )
        flash(f"Successfully updated details for {name}", "success")
    else:
        flash("Error: Missing Visitor Name", "danger")
        
    return redirect(url_for('admin.manage_visitors'))"""

# 2. Update manage_other
target2 = """@admin.route('/manage_other', methods=['GET'])
def manage_other():
    from models.vector_db import other_collection
    
    try:
        results = other_collection.get()
        other_names = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        total_count = len(other_names)
        
        # Combine names and roles
        external_staff = []
        for i in range(total_count):
            name = other_names[i]
            role = metadatas[i].get('Role', 'Unknown') if metadatas and i < len(metadatas) and metadatas[i] else 'Unknown'
            external_staff.append({"name": name, "role": role})
            
    except Exception as e:
        print(f"[ERROR] Could not fetch external staff: {e}")
        external_staff = []
        total_count = 0
        flash("Failed to load external staff from database.", "danger")
        
    return render_template('manage_other.html', external_staff=external_staff, total_count=total_count)"""

replace2 = """@admin.route('/manage_other', methods=['GET'])
def manage_other():
    from models.vector_db import other_collection
    from models.database import universal_registry
    
    try:
        results = other_collection.get()
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
                external_staff.append({"Name": name, "Role": role, "Phone": "Unknown", "Email": "Unknown"})
                
    except Exception as e:
        print(f"[ERROR] Could not fetch external staff: {e}")
        external_staff = []
        total_count = 0
        flash("Failed to load external staff from database.", "danger")
        
    return render_template('manage_other.html', external_staff=external_staff, total_count=total_count)

@admin.route('/update_other_details', methods=['POST'])
def update_other_details():
    from models.database import universal_registry
    import datetime
    
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    role = request.form.get('role', 'Unknown')
    
    if name:
        clean_name = name.replace(" ", "").upper()
        smart_id = f"EXTSTF-{clean_name}"
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        universal_registry.update_one(
            {"_id": smart_id},
            {
                "$set": {
                    "Email": email,
                    "Phone": phone,
                    "Role": role
                },
                "$setOnInsert": {
                    "Name": name,
                    "Address": "Unknown",
                    "Visitor_Type": "Regular",
                    "Date": today_str,
                    "In_Time": None,
                    "Out_Time": None
                }
            },
            upsert=True
        )
        flash(f"Successfully updated details for {name}", "success")
    else:
        flash("Error: Missing Staff Name", "danger")
        
    return redirect(url_for('admin.manage_other'))"""

if target1 in content:
    content = content.replace(target1, replace1)
    print("Replaced target 1")
else:
    print("Could not find target 1")
    
if target2 in content:
    content = content.replace(target2, replace2)
    print("Replaced target 2")
else:
    print("Could not find target 2")

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'w') as f:
    f.write(content)
