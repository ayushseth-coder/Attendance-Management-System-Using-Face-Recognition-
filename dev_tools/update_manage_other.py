with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'r') as f:
    content = f.read()

target = """@admin.route('/manage_other', methods=['GET'])
def manage_other():
    from models.vector_db import other_collection
    
    try:
        results = other_collection.get(include=["metadatas"])
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

replace = """@admin.route('/manage_other', methods=['GET'])
def manage_other():
    from models.vector_db import other_collection
    from models.database import universal_registry
    
    try:
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

if target in content:
    content = content.replace(target, replace)
    with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'w') as f:
        f.write(content)
    print("Success")
else:
    print("Failed")
