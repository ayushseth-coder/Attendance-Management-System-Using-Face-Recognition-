with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'r') as f:
    content = f.read()

target = '''@admin.route('/update_employee_details', methods=['POST'])
def update_employee_details():
    from models.database import collection
    import datetime
    
    name = request.form.get('name')
    email = request.form.get('email')
    job = request.form.get('job')
    
    if name:
        # Upsert: Update if exists, Insert if not
        collection.update_one(
            {"Name": name},
            {
                "$set": {
                    "Email": email, 
                    "Job": job,
                    "Phone": request.form.get('phone', 'N/A')
                },
                "$setOnInsert": {
                    "Date": datetime.datetime.now(),
                    "Password": ""  # Require password reset if they want to login later
                }
            },
            upsert=True
        )
        flash(f"Successfully updated details for {name}", "success")
    else:
        flash("Error: Missing Employee Name", "danger")
        
    return redirect(request.referrer or url_for('admin.manage_employees'))'''

replacement = '''@admin.route('/update_employee_details', methods=['POST'])
def update_employee_details():
    from models.database import collection, universal_registry
    import datetime
    import re
    
    name = request.form.get('name')
    email = request.form.get('email')
    job = request.form.get('job')
    phone = request.form.get('phone', 'Unknown')
    address = request.form.get('address', 'Unknown')
    leave_status = request.form.get('leave_status', 'Active')
    
    if name:
        # 1. Update Old Architecture
        collection.update_one(
            {"Name": name},
            {
                "$set": {
                    "Email": email, 
                    "Job": job,
                    "Phone": phone,
                    "Address": address,
                    "Leave_Status": leave_status
                },
                "$setOnInsert": {
                    "Date": datetime.datetime.now(),
                    "Password": ""
                }
            },
            upsert=True
        )
        
        # 2. Update Shadow Architecture
        try:
            match = re.match(r"([A-Za-z]+)(\\d*)", name)
            if match:
                clean_name = match.group(1).capitalize()
                extracted_id = match.group(2) if match.group(2) else None
            else:
                clean_name = name.capitalize()
                extracted_id = None
                
            smart_id = f"EMP-{extracted_id}" if extracted_id else f"EMP-{clean_name.upper()}"
            
            universal_registry.update_one(
                {"_id": smart_id},
                {
                    "$set": {
                        "Email": email,
                        "Phone": phone,
                        "Address": address,
                        "Leave_Status": leave_status
                    }
                }
            )
        except Exception as e:
            print(f"[SHADOW DB ERROR] Failed to sync update: {e}")
            
        flash(f"Successfully updated details for {name}", "success")
    else:
        flash("Error: Missing Employee Name", "danger")
        
    return redirect(request.referrer or url_for('admin.manage_employees'))'''

if target in content:
    content = content.replace(target, replacement)
    with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'w') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found!")
