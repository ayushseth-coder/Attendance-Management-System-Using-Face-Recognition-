from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from werkzeug.security import generate_password_hash
from models.database import collection, adminlog, securitylog,visitorlogtable,activevisitorstable,reqvistable,rejectedvistable,visitors_status
from datetime import datetime
from flask_bcrypt import Bcrypt
from bson import ObjectId
from collections import defaultdict
from flask import json

admin = Blueprint('admin', __name__)
bcrypt = Bcrypt()

@admin.before_request
def require_admin_login():
    # Allow static files if they are served through this blueprint (usually they aren't, but just in case)
    if request.endpoint and 'static' in request.endpoint:
        return
    # Check if user is logged in and has the admin role
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("You do not have permission to access the admin portal.", "danger")
        return redirect(url_for('auth.login'))


# OLD GLOBAL CODE - Commented out to make Dashboard dynamic
# visitobj = list(visitorlogtable.find())
# activeobj = list(activevisitorstable.find())
# rejectobj = list(rejectedvistable.find())
# adminobj = list(adminlog.find())
# secobj = list(securitylog.find())
# reqobj = list(reqvistable.find())
# pending=len(reqobj)
# reject=len(rejectobj)
# countvis = len(visitobj)
# active = len(activeobj)
# total=reject+countvis

@admin.context_processor
def inject_pending_count():
    # Makes pending_count available to all admin templates for the notification badge
    reqobj = list(reqvistable.find())
    return dict(pending_count=len(reqobj))


@admin.route('/admindash')
def admindash():
    # Dynamically compute stats on every page load
    pending = len(list(reqvistable.find()))
    reject = len(list(rejectedvistable.find()))
    countvis = len(list(visitorlogtable.find()))
    active = len(list(activevisitorstable.find()))
    total = reject + countvis

    global months,accept_data,total_data
    all_visitors = list(visitors_status.find({}))  

    monthly_stats = defaultdict(lambda: {"accept": 0, "total": 0})

    for visitor in all_visitors:
        if 'Date' in visitor:
            dt = visitor['Date']
           
            if isinstance(dt, str):
                try:
                      dt = datetime.fromisoformat(dt)
                except ValueError:
                    continue  

            month = dt.strftime("%b")  
            monthly_stats[month]["total"] += 1
            if visitor.get("status") == "accept":
                monthly_stats[month]["accept"] += 1

    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    accept_data = [monthly_stats[m]["accept"] for m in months]
    total_data = [monthly_stats[m]["total"] for m in months]
    



    return render_template('admin_h.html',pending=pending ,total=total,countvis=countvis, active=active,rejectobj=reject,
                           months=months, accept_data=accept_data, total_data=total_data)


@admin.route('/addadmin', methods=['POST'])
def add_admin():
    if request.method == 'POST':
        Name = request.form.get('fullname', '').strip()
        Email = request.form.get('addemail', '').strip()
        Phone = request.form.get('phone', '').strip()
        Job = request.form.get('jobtitle', '').strip()
        Password = request.form.get('password', '')
        PasswordConf = request.form.get('passwordConfirmation', '')
        
        # 1. Check for empty fields
        if not Name or not Email or not Phone or not Job or not Password:
            flash("All fields are required.", "danger")
            return redirect(request.referrer or url_for('admin.filter_role'))
            
        # 2. Check if passwords match
        if Password != PasswordConf:
            flash("Passwords do not match.", "danger")
            return redirect(request.referrer or url_for('admin.filter_role'))
            
        # 3. Check for duplicate Email
        if collection.find_one({"Email": Email}):
            flash("An account with this Email already exists.", "danger")
            return redirect(request.referrer or url_for('admin.filter_role'))
            
        # 4. Check for duplicate Phone
        if collection.find_one({"Phone": Phone}):
            flash("An account with this Phone number already exists.", "danger")
            return redirect(request.referrer or url_for('admin.filter_role'))
            
        # Insert new user if all validations pass
        today = datetime.now()
        hashed_password = generate_password_hash(Password)
        
        new_admin = {
            "Name": Name,
            "Email": Email,
            "Phone": Phone,
            "Date": today,
            "Job": Job,
            "Password": hashed_password 
        }
        
        collection.insert_one(new_admin)
        if Job.lower() == 'admin':
            adminlog.insert_one(new_admin)
        elif Job.lower() == 'security':
            securitylog.insert_one(new_admin)
            
        flash(f"Account for {Name} created successfully!", "success")
        return redirect(request.referrer or url_for('admin.filter_role'))
@admin.route('/deleteuser/<string:Phone>', methods=['POST', 'GET'])
def deleteuser(Phone):
    collection.delete_one({"Phone": Phone})
    securitylog.delete_one({"Phone": Phone})
    adminlog.delete_one({"Phone": Phone})
    return redirect(url_for('admin.admindash'))


# @admin.route('/updateusers/<id>', methods=['POST', 'GET'])
# def updateusers(id):
#     users = collection.db.users
#     items = users.find_one({'_id': ObjectId(id)})

#     if request.method == 'POST':
#         if request.form['submit'] == 'pass':
#             myquery = {'_id': ObjectId(id)}

#             updatelog = {"$set":
#                              {"Name": request.form.get('Name'),
#                               "Email": request.form.get('Email'),
#                               "Phone": request.form.get('Phone'),
#                               "Job": request.form.get('Job'),
#                               "Password": request.files.get('Password'),
#                               "date": datetime.datetime.utcnow()
#                               }
#                          }

#     adminlog.update_one(myquery, updatelog)
#     collection.update_one(myquery, updatelog)
#     securitylog.update_one(myquery, updatelog)

    # return redirect(url_for('admin.admindash'))

@admin.route('/edituser/<string:Phone>', methods=['GET','POST'])
def edituser():
    phone = request.args.get('Phone')
    user = collection.find_one({"Phone": phone})

    return render_template('user_overview.html')

@admin.route("/notification",methods=['POst','GET'])
def notification():
    reqobj = list(reqvistable.find())
    return render_template ('Notification.html',reqobj=reqobj) 


@admin.route("/filter_role", methods=['GET'])  # dropdown filtering
def filter_role():
    status = request.args.get('role', 'all')
    
    # Only allow legitimate Dashboard Access users to appear on the User Overview page.
    # We do this by ensuring they actually have a Password (facial recognition employees have Password="").
    base_query = {"Password": {"$ne": ""}}
    
    if status.lower() == 'all':
        query = base_query
    else:
        query = {
            "$and": [
                base_query,
                {"Job": {"$regex": f"^{status}$", "$options": "i"}}
            ]
        }

    users = list(collection.find(query))  
    return render_template('user_overview.html', users=users, selected_role=status)


@admin.route("/visitor_over",methods=['POst','GET'])
def visitor_over():

    status = request.args.get('status', 'all')
    query = {} if status == 'all' else {"status": status}

    users = list(visitors_status.find(query))  
    return render_template('visitor_overview.html', users=users, status_filter=status) 


@admin.route("/admin_h",methods=['POst','GET'])
def admin_h():
    # Dynamically compute stats on every page load
    pending = len(list(reqvistable.find()))
    reject = len(list(rejectedvistable.find()))
    countvis = len(list(visitorlogtable.find()))
    active = len(list(activevisitorstable.find()))
    total = reject + countvis

    global months,accept_data,total_data
    all_visitors = list(visitors_status.find({}))  

    monthly_stats = defaultdict(lambda: {"accept": 0, "total": 0})

    for visitor in all_visitors:
        if 'Date' in visitor:
            dt = visitor['Date']
            # Convert string to datetime if needed
            if isinstance(dt, str):
                try:
                      dt = datetime.fromisoformat(dt)
                except ValueError:
                    continue  

            month = dt.strftime("%b")  
            monthly_stats[month]["total"] += 1
            if visitor.get("status") == "accept":
                monthly_stats[month]["accept"] += 1

    #  month order for the chart
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    accept_data = [monthly_stats[m]["accept"] for m in months]
    total_data = [monthly_stats[m]["total"] for m in months]
    return render_template ("admin_h.html",  pending=pending ,total=total,countvis=countvis, active=active,rejectobj=reject,
                           months=months, accept_data=accept_data, total_data=total_data)  

@admin.route('/enroll_employees', methods=['GET', 'POST'])
def enroll_employees():
    if request.method == 'GET':
        return render_template('enroll_employee.html')
    
    if request.method == 'POST':
        import os
        from werkzeug.utils import secure_filename
        from deepface import DeepFace
        from models.vector_db import employee_collection
        
        if 'employee_images' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        files = request.files.getlist('employee_images')
        if not files or files[0].filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
        os.makedirs(faces_dir, exist_ok=True)
        
        success_count = 0
        error_count = 0
        
        for file in files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filename = secure_filename(file.filename)
                filepath = os.path.join(faces_dir, filename)
                file.save(filepath)
                
                # Extract Name from filename (e.g. "Anshuman.jpg" -> "Anshuman")
                employee_name = os.path.splitext(filename)[0].capitalize()
                
                try:
                    # Run AI Extraction
                    # representations = DeepFace.represent(img_path=filepath, model_name="Facenet", enforce_detection=False)
                    representations = DeepFace.represent(img_path=filepath, model_name="ArcFace", enforce_detection=False)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        
                        # Save to Vector DB
                        employee_collection.upsert(
                            ids=[employee_name],
                            embeddings=[embedding],
                            metadatas=[{"path": filepath}]
                        )
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to process {filename}: {e}")
                    error_count += 1
                    
        if success_count > 0:
            flash(f'Successfully enrolled {success_count} employee(s) into the Biometric Database!', 'success')
        if error_count > 0:
            flash(f'Failed to process {error_count} file(s). Ensure they contain clear faces.', 'danger')
            
        return redirect(url_for('admin.enroll_employees'))

@admin.route('/manage_employees', methods=['GET'])
def manage_employees():
    from models.vector_db import employee_collection
    from models.database import collection
    
    try:
        results = employee_collection.get(include=["metadatas"])
        employee_ids = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        total_count = len(employee_ids)
        
        # Cross-reference with the users collection
        all_users = list(collection.find())
        user_lookup = {}
        for user in all_users:
            name = user.get("Name", "")
            if name:
                user_lookup[name] = {
                    "Email": user.get("Email", "Unknown"),
                    "Job": user.get("Job", "Unknown"),
                    "Phone": user.get("Phone", "Unknown"),
                    "Address": user.get("Address", "Unknown"),
                    "Leave_Status": user.get("Leave_Status", "Active")
                }
                
        unique_employees = {}
        for i in range(total_count):
            chroma_id = employee_ids[i]
            
            hr_id = metadatas[i].get("HR_ID", chroma_id) if metadatas and i < len(metadatas) and metadatas[i] else chroma_id
            
            real_name = metadatas[i].get("Name", hr_id) if metadatas and i < len(metadatas) and metadatas[i] else hr_id
            
            if real_name not in unique_employees:
                user_info = user_lookup.get(real_name, {"Email": "Unknown", "Job": "Unknown", "Phone": "Unknown", "Address": "Unknown", "Leave_Status": "Active"})
                unique_employees[real_name] = {
                    "emp_id": hr_id,
                    "HR_ID": hr_id,
                    "Name": real_name,
                    "Email": user_info.get("Email", "Unknown"),
                    "Job": user_info.get("Job", "Unknown"),
                    "Phone": user_info.get("Phone", "Unknown"),
                    "Address": user_info.get("Address", "Unknown"),
                    "Leave_Status": user_info.get("Leave_Status", "Active"),
                    "Photo_Count": 1,
                    "chroma_ids": [chroma_id]
                }
            else:
                unique_employees[real_name]["Photo_Count"] += 1
                unique_employees[real_name]["chroma_ids"].append(chroma_id)
                
        employees_data = list(unique_employees.values())
        total_unique_count = len(employees_data)
    except Exception as e:
        print(f"[ERROR] Could not fetch employees: {e}")
        employees_data = []
        total_unique_count = 0
        total_count = 0
        flash("Failed to load employees from database.", "danger")
        
    return render_template('manage_employees.html', employees_data=employees_data, total_count=total_count, unique_count=total_unique_count)

@admin.route('/delete_employee/<name>', methods=['POST'])
def delete_employee(name):
    from models.vector_db import employee_collection
    
    try:
        # Delete from ChromaDB
        employee_collection.delete(ids=[name])
        flash(f"Successfully deleted records for ID {name}.", "success")
        
        # Cleanup: Delete ALL local photos matching the employee name (ignoring case and extensions)
        import os
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                # If the name matches (ignoring capital letters), delete it!
                if name_without_ext.lower() == name.lower():
                    try:
                        os.remove(os.path.join(faces_dir, filename))
                    except Exception:
                        pass
                
    except Exception as e:
        flash(f"Error deleting {name}: {e}", "danger")
        
    return redirect(url_for('admin.manage_employees'))

@admin.route('/delete_all_employees', methods=['POST'])
def delete_all_employees():
    from models.vector_db import employee_collection
    import os
    
    try:
        # 1. Fetch all IDs
        results = employee_collection.get()
        all_ids = results.get('ids', [])
        
        # 2. Wipe ChromaDB
        if all_ids:
            employee_collection.delete(ids=all_ids)
            
        # 3. Nuclear Scrub of employee_faces folder (only deleting images, protecting DeepFace .pkl files)
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
        deleted_files_count = 0
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(faces_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_files_count += 1
                    except Exception:
                        pass
                        
        flash(f"SYSTEM WIPED: Successfully deleted {len(all_ids)} vectors from ChromaDB and {deleted_files_count} physical photos from the server.", "success")
        
    except Exception as e:
        flash(f"Error wiping database: {e}", "danger")
        
    return redirect(url_for('admin.manage_employees'))

@admin.route('/manage_section', methods=['GET'])
def manage_section():
    if session.get('logged_in'):
        return render_template('manage_section.html')
    else:
        return redirect(url_for('auth.login'))

@admin.route('/manage_visitors', methods=['GET'])
def manage_visitors():
    from models.vector_db import visitor_collection
    from models.database import universal_registry
    
    try:
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
                visitor_profiles.append({"num_id": vis_id, "Name": name, "Phone": "Unknown", "Email": "Unknown"})
                
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
    
    visitor_id = request.form.get('visitor_id')
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    
    if visitor_id and name:
        smart_id = f"REGVIS-{visitor_id}"
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
        
    return redirect(url_for('admin.manage_visitors'))

@admin.route('/delete_visitor/<visitor_id>', methods=['POST'])
def delete_visitor(visitor_id):
    from models.vector_db import visitor_collection
    
    try:
        # Delete from ChromaDB
        visitor_collection.delete(ids=[visitor_id])
        flash(f"Successfully deleted records for ID {visitor_id}.", "success")
        
        # Cleanup: Delete local photo
        import os
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                if name_without_ext.lower() == visitor_id.lower():
                    try:
                        os.remove(os.path.join(faces_dir, filename))
                    except Exception:
                        pass
                
    except Exception as e:
        flash(f"Error deleting {visitor_id}: {e}", "danger")
        
    return redirect(url_for('admin.manage_visitors'))

@admin.route('/delete_all_visitors', methods=['POST'])
def delete_all_visitors():
    from models.vector_db import visitor_collection
    import os
    
    try:
        results = visitor_collection.get()
        all_ids = results.get('ids', [])
        
        if all_ids:
            visitor_collection.delete(ids=all_ids)
            
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
        deleted_files_count = 0
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(faces_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_files_count += 1
                    except Exception:
                        pass
                        
        flash(f"SYSTEM WIPED: Successfully deleted {len(all_ids)} visitor vectors from ChromaDB and {deleted_files_count} physical photos.", "success")
        
    except Exception as e:
        flash(f"Error wiping database: {e}", "danger")
        
    return redirect(url_for('admin.manage_visitors'))

@admin.route('/manage_other', methods=['GET'])
def manage_other():
    from models.vector_db import other_collection
    from models.database import universal_registry
    
    try:
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
                external_staff.append({"num_id": stf_id, "Name": name, "Role": role, "Phone": "Unknown", "Email": "Unknown"})
                
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
    
    staff_id = request.form.get('staff_id')
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    phone = request.form.get('phone', 'Unknown')
    role = request.form.get('role', 'Unknown')
    
    if staff_id and name:
        smart_id = f"EXTSTF-{staff_id}"
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
        
    return redirect(url_for('admin.manage_other'))

@admin.route('/delete_other/<staff_id>', methods=['POST'])
def delete_other(staff_id):
    from models.vector_db import other_collection
    
    try:
        other_collection.delete(ids=[staff_id])
        flash(f"Successfully deleted records for ID {staff_id}.", "success")
        
        import os
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                if name_without_ext.lower() == staff_id.lower():
                    try:
                        os.remove(os.path.join(faces_dir, filename))
                    except Exception:
                        pass
                
    except Exception as e:
        flash(f"Error deleting {staff_id}: {e}", "danger")
        
    return redirect(url_for('admin.manage_other'))

@admin.route('/delete_all_other', methods=['POST'])
def delete_all_other():
    from models.vector_db import other_collection
    import os
    
    try:
        results = other_collection.get()
        all_ids = results.get('ids', [])
        
        if all_ids:
            other_collection.delete(ids=all_ids)
            
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
        deleted_files_count = 0
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(faces_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_files_count += 1
                    except Exception:
                        pass
                        
        flash(f"SYSTEM WIPED: Successfully deleted {len(all_ids)} external staff vectors from ChromaDB and {deleted_files_count} physical photos.", "success")
        
    except Exception as e:
        flash(f"Error wiping database: {e}", "danger")
        
    return redirect(url_for('admin.manage_other'))

@admin.route('/attendance/select', methods=['GET'])
def attendance_select():
    return render_template('attendance_select.html')

@admin.route('/attendance/employee', methods=['GET'])
def attendance_employee():
    from models.database import attendance_log
    import datetime
    
    # Get date from query params, default to today
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    # Query MongoDB for records where Date starts with the selected date string
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": "Present"
    }
    logs = list(attendance_log.find(query).sort("Date", -1)) # Sort newest first
    
    return render_template('attendance_employee.html', logs=logs, selected_date=selected_date)

@admin.route('/employee_image/<name>')
def employee_image(name):
    import os
    from flask import send_from_directory, abort
    
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
    
    # Search for the exact file case-insensitively
    if os.path.exists(faces_dir):
        for filename in os.listdir(faces_dir):
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext.lower() == name.lower():
                return send_from_directory(faces_dir, filename)
                
    # If physical image was deleted, serve a clean SVG placeholder instead of a broken image
    svg_data = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#adb5bd">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>'''
    from flask import Response
    return Response(svg_data, mimetype='image/svg+xml')

@admin.route('/attendance/visitor', methods=['GET'])
def attendance_visitor():
    from models.database import attendance_log
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": "Regular Visitor"
    }
    logs = list(attendance_log.find(query).sort("Date", -1))
    
    return render_template('attendance_visitor.html', logs=logs, selected_date=selected_date)

@admin.route('/visitor_image/<name>')
def visitor_image(name):
    import os
    from flask import send_from_directory, abort
    
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
    
    if os.path.exists(faces_dir):
        for filename in os.listdir(faces_dir):
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext.lower() == name.lower():
                return send_from_directory(faces_dir, filename)
                
    svg_data = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#adb5bd">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>'''
    from flask import Response
    return Response(svg_data, mimetype='image/svg+xml')

@admin.route('/attendance/other', methods=['GET'])
def attendance_other():
    from models.database import attendance_log
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": {"$regex": r"^Present \("}
    }
    logs = list(attendance_log.find(query).sort("Date", -1))
    
    return render_template('attendance_other.html', logs=logs, selected_date=selected_date)

@admin.route('/other_image/<name>')
def other_image(name):
    import os
    from flask import send_from_directory, abort
    
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
    
    if os.path.exists(faces_dir):
        for filename in os.listdir(faces_dir):
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext.lower() == name.lower():
                return send_from_directory(faces_dir, filename)
                
    svg_data = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#adb5bd">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>'''
    from flask import Response
    return Response(svg_data, mimetype='image/svg+xml')

@admin.route('/attendance/timesheet', methods=['GET'])
def attendance_timesheet():
    from models.database import attendance_log, collection
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    # 1. Fetch raw logs for the selected date (Only Employees)
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": "Present"
    }
    raw_logs = list(attendance_log.find(query).sort("Date", -1))
    
    # 2. Fetch Users collection to get Emails and Roles
    all_users = list(collection.find())
    # Create a quick lookup dictionary: {"John Doe": {"Email": "john@x.com", "Job": "Developer"}}
    user_lookup = {}
    for user in all_users:
        name = user.get("Name", "")
        if name:
            user_lookup[name] = {
                "Email": user.get("Email", "N/A"),
                "Job": user.get("Job", "Employee")
            }
            
    # 3. Build the consolidated Timesheet
    timesheet_data = []
    for log in raw_logs:
        name = log.get("Name", "")
        entry_datetime_str = log.get("Date", "")  # e.g. "2026-06-19 09:00:00"
        exit_time_str = log.get("ExitTime")       # e.g. "17:00:00" or None
        
        # Extract just the time from entry_datetime_str
        entry_time_str = entry_datetime_str.split(' ')[1] if ' ' in entry_datetime_str else entry_datetime_str
        
        # Calculate Working Hours
        working_hours = None
        if exit_time_str and ' ' in entry_datetime_str:
            try:
                fmt = '%H:%M:%S'
                t1 = datetime.datetime.strptime(entry_time_str, fmt)
                t2 = datetime.datetime.strptime(exit_time_str, fmt)
                
                # Handle cases where exit is past midnight (though rare for a day-based scan)
                if t2 < t1:
                    t2 += datetime.timedelta(days=1)
                    
                diff = t2 - t1
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                working_hours = f"{hours}h {minutes}m"
            except Exception as e:
                print(f"[ERROR] Failed to calculate working hours for {name}: {e}")
                working_hours = "Error"
                
        # Lookup User Info
        user_info = user_lookup.get(name, {"Email": "Unknown", "Job": "Unknown"})
        
        timesheet_data.append({
            "Name": name,
            "Email": user_info["Email"],
            "Job": user_info["Job"],
            "EntryTime": entry_time_str,
            "ExitTime": exit_time_str,
            "WorkingHours": working_hours
        })
        
    return render_template('attendance_timesheet.html', timesheet=timesheet_data, selected_date=selected_date)

@admin.route('/update_employee_details', methods=['POST'])
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
            match = re.match(r"([A-Za-z]+)(\d*)", name)
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
        
    return redirect(request.referrer or url_for('admin.manage_employees'))

@admin.route('/universal_records', methods=['GET'])
def universal_records():
    from models.database import universal_registry
    
    # Fetch all records from the Shadow Database
    try:
        records = list(universal_registry.find().sort("Name", 1))
    except Exception as e:
        print(f"[ERROR] Fetching Universal Records: {e}")
        records = []
        flash("Failed to load Universal Records.", "danger")
        
    return render_template('universal_records.html', records=records)
