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
    from datetime import timedelta
    from models.database import attendance_log
    
    # Dynamically compute stats on every page load
    pending = len(list(reqvistable.find()))
    reject = len(list(rejectedvistable.find()))
    countvis = len(list(visitorlogtable.find()))
    active = len(list(activevisitorstable.find()))
    total = reject + countvis

    # ---------------------------------------------------------
    # NEW: Day-wise Present Employee Attendance Time Series
    # ---------------------------------------------------------
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = datetime.today().date()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        # Default to exactly 5 days before end_date to make a 6-day window
        start_date = end_date - timedelta(days=5)

    # Generate the list of dates for the labels
    date_labels = []
    daily_attendance = {}
    
    current_dt = start_date
    while current_dt <= end_date:
        label = current_dt.strftime("%b %d")
        date_labels.append(label)
        daily_attendance[current_dt.strftime("%Y-%m-%d")] = set()
        current_dt += timedelta(days=1)

    # Query attendance_log between start_date and end_date
    query = {
        "Date": {
            "$gte": start_date.strftime("%Y-%m-%d"),
            "$lt": (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
        }
    }
    
    logs = list(attendance_log.find(query))
    
    for log in logs:
        log_date_full = log.get("Date", "")
        # Extract just the YYYY-MM-DD from YYYY-MM-DD HH:MM:SS
        log_date = log_date_full.split(" ")[0] if " " in log_date_full else log_date_full
        
        name = log.get("Name")
        if log_date in daily_attendance and name:
            daily_attendance[log_date].add(name)

    # Extract the counts in the same order as date_labels
    employee_counts = []
    current_dt = start_date
    while current_dt <= end_date:
        date_str = current_dt.strftime("%Y-%m-%d")
        employee_counts.append(len(daily_attendance[date_str]))
        current_dt += timedelta(days=1)

    # ---------------------------------------------------------
    # NEW: Date-Specific Total Attendance Pie Chart
    # ---------------------------------------------------------
    pie_date_str = request.args.get('pie_date')
    if not pie_date_str:
        pie_date_str = datetime.today().strftime("%Y-%m-%d")
    
    # 1. Present Employees (Checked in on pie_date)
    present_employees_query = attendance_log.find({"Date": {"$regex": f"^{pie_date_str}"}})
    present_employee_names = set()
    for log in present_employees_query:
        if log.get("Name"):
            present_employee_names.add(log.get("Name"))
    present_employees_list = list(present_employee_names)
    present_emp_count = len(present_employees_list)

    # 2. Present Visitors (Historically present on pie_date, Registration_Role == "Visitor")
    active_visitors_query = visitorlogtable.find({"Date": pie_date_str, "Registration_Role": "Visitor"})
    present_visitors_list = list(set([v.get("Name", "Unknown") for v in active_visitors_query]))
    present_vis_count = len(present_visitors_list)

    # 3. Present External Staff (Historically present on pie_date, Registration_Role != "Visitor" and != "Employee")
    active_external_query = visitorlogtable.find({"Date": pie_date_str, "Registration_Role": {"$nin": ["Visitor", "Employee"]}})
    present_external_list = list(set([v.get("Name", "Unknown") for v in active_external_query]))
    present_ext_count = len(present_external_list)

    # 4. Calculate overall totals for dashboard cards
    from models.vector_db import employee_collection, visitor_collection, other_collection

    # Employees (Unique count from ChromaDB, grouped by HR_ID)
    try:
        emp_res = employee_collection.get(include=["metadatas"])
        emp_metas = emp_res.get("metadatas", [])
        unique_emp_ids = set([m.get("HR_ID") for m in emp_metas if m and m.get("HR_ID")])
        total_employees = len(unique_emp_ids)
        
        # For the dropdown list, show Name (HR_ID) to distinguish them
        unique_emp_names = set([f"{m.get('Name', 'Unknown')} ({m.get('HR_ID', 'Unknown')})" for m in emp_metas if m and m.get("HR_ID")])
        employee_names = list(unique_emp_names)
    except:
        total_employees = 0
        employee_names = []

    # Regular Visitors (Unique count from ChromaDB)
    try:
        vis_res = visitor_collection.get(include=["documents"])
        unique_vis = set([doc for doc in vis_res.get("documents", []) if doc])
        total_regular_visitors = len(unique_vis)
        regular_visitor_names = list(unique_vis)
    except:
        total_regular_visitors = 0
        regular_visitor_names = []

    # External Staff (Unique count from ChromaDB)
    try:
        ext_res = other_collection.get(include=["documents"])
        unique_ext = set([doc for doc in ext_res.get("documents", []) if doc])
        total_external_staff = len(unique_ext)
        external_staff_names = list(unique_ext)
    except:
        total_external_staff = 0
        external_staff_names = []

    # Pending Requests (from reqvistable)
    pending_query = list(reqvistable.find())
    pending_request_names = [req.get("Name", "Unknown") for req in pending_query]
    # 'pending' is already calculated as len(pending_query) at line 50

    return render_template('admin_h.html',
                           pending=pending, total=total, countvis=countvis, active=active, rejectobj=reject,
                           chart_labels=date_labels, chart_data=employee_counts,
                           start_date=start_date.strftime("%Y-%m-%d"),
                           end_date=end_date.strftime("%Y-%m-%d"),
                           pie_date=pie_date_str,
                           present_emp_count=present_emp_count,
                           present_vis_count=present_vis_count,
                           present_ext_count=present_ext_count,
                           present_employees_list=present_employees_list,
                           present_visitors_list=present_visitors_list,
                           present_external_list=present_external_list,
                           total_employees=total_employees,
                           employee_names=employee_names,
                           total_regular_visitors=total_regular_visitors,
                           regular_visitor_names=regular_visitor_names,
                           total_external_staff=total_external_staff,
                           external_staff_names=external_staff_names,
                           pending_request_names=pending_request_names)


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
    return redirect(url_for('admin.admindash'))


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
                    representations = DeepFace.represent(img_path=filepath, model_name="ArcFace", enforce_detection=True)
                    
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
            raw_name = user.get("Name", "")
            if raw_name:
                import re
                match = re.match(r"([A-Za-z]+)[_-]?(\d*)", raw_name.strip().capitalize())
                if match:
                    clean_name = match.group(1).capitalize()
                    extracted_id = match.group(2)
                else:
                    clean_name = raw_name.strip().capitalize()
                    extracted_id = ""
                    
                hr_id = f"EMP-{extracted_id}" if extracted_id else f"EMP-{clean_name.upper()}"
                    
                user_lookup[hr_id] = {
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
            
            if hr_id not in unique_employees:
                user_info = user_lookup.get(hr_id, {"Email": "Unknown", "Job": "Unknown", "Phone": "Unknown", "Address": "Unknown", "Leave_Status": "Active"})
                
                # Show Name (ID) if we want to be safe, but they are already separated into different rows
                unique_employees[hr_id] = {
                    "emp_id": hr_id,
                    "HR_ID": hr_id,
                    "Name": f"{real_name} ({hr_id})",
                    "Email": user_info.get("Email", "Unknown"),
                    "Job": user_info.get("Job", "Unknown"),
                    "Phone": user_info.get("Phone", "Unknown"),
                    "Address": user_info.get("Address", "Unknown"),
                    "Leave_Status": user_info.get("Leave_Status", "Active"),
                    "Photo_Count": 1,
                    "chroma_ids": [chroma_id]
                }
            else:
                unique_employees[hr_id]["Photo_Count"] += 1
                unique_employees[hr_id]["chroma_ids"].append(chroma_id)
                
        employees_data = list(unique_employees.values())
        total_unique_count = len(employees_data)
    except Exception as e:
        print(f"[ERROR] Could not fetch employees: {e}")
        employees_data = []
        total_unique_count = 0
        total_count = 0
        flash("Failed to load employees from database.", "danger")
        
    return render_template('manage_employees.html', employees_data=employees_data, total_count=total_count, unique_count=total_unique_count)

@admin.route('/employee/detail/<employee_id>', methods=['GET'])
def employee_detail(employee_id):
    from models.vector_db import employee_collection
    from models.database import collection
    import os
    import re
    
    try:
        # STEP 1: Direct ID search (Fast & Clean)
        user_info = collection.find_one({"ID": employee_id})
        
        # STEP 2: Fallback for older legacy records (where ID was embedded in Name)
        if not user_info:
            for user in collection.find():
                match = re.match(r"([A-Za-z]+)[_-]?(\d*)", user.get("Name", "").strip().capitalize())
                if match and match.group(2) and employee_id == f"EMP-{match.group(2)}":
                    user_info = user
                    break
                        
        if not user_info:
            flash(f"Employee with ID {employee_id} not found in database.", "warning")
            return redirect(url_for('admin.manage_employees'))
            
        # Fetch ChromaDB data for vector/photo count
        photo_count = 0
        real_name = user_info.get("Name", employee_id)
        
        if employee_collection is not None:
            try:
                results = employee_collection.get(include=["metadatas"])
                metadatas = results.get('metadatas', [])
                for meta in metadatas:
                    if meta:
                        hr_id = meta.get("HR_ID")
                        if str(hr_id) == str(employee_id):
                            photo_count += 1
                            real_name = meta.get("Name", real_name)
            except Exception as chroma_err:
                print(f"[WARNING] ChromaDB query note: {chroma_err}")

                    
        # Fetch dynamic role stored in database
        db_role = user_info.get("Role") or user_info.get("Registration_Role") or user_info.get("role")
        if not db_role or str(db_role).lower() == "employee":
            db_role = user_info.get("Job") or "Employee"

        # Fetch Attendance logs for Present dates, Late dates, & Daily Activity
        from models.database import attendance_log
        import datetime

        present_dates = []
        late_dates = []
        recent_activity = []

        try:
            attendance_records = list(attendance_log.find({
                "$or": [
                    {"ID": str(employee_id)},
                    {"HR_ID": str(employee_id)},
                    {"Name": real_name}
                ]
            }).sort("Date", -1))

            for rec in attendance_records:
                d_val = rec.get("Date") or rec.get("date")
                if d_val:
                    d_str = str(d_val).split(" ")[0]
                    if d_str not in present_dates:
                        present_dates.append(d_str)

                    # Extract entry & exit time (Office Timing: 10:00 AM - 6:30 PM)
                    entry_time_full = str(d_val)
                    entry_time = entry_time_full.split(" ")[1] if " " in entry_time_full else "10:00:00"
                    exit_time = rec.get("ExitTime") or rec.get("exit_time") or "18:30:00"

                    # Check late status (Office Timing: 10:00 AM, Late consider after 10:30 AM)
                    is_late = False
                    try:
                        entry_h, entry_m = map(int, entry_time.split(":")[:2])
                        if entry_h > 10 or (entry_h == 10 and entry_m > 30):
                            is_late = True
                            if d_str not in late_dates:
                                late_dates.append(d_str)
                    except Exception:
                        pass

                    # Build Daily Activity List Item
                    try:
                        dt_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d")
                        day_name = dt_obj.strftime("%A")
                        day_num = dt_obj.strftime("%d")
                        month_short = dt_obj.strftime("%b").upper()

                        t1 = datetime.datetime.strptime(entry_time[:5], "%H:%M")
                        t2 = datetime.datetime.strptime(exit_time[:5], "%H:%M")
                        if t2 < t1:
                            t2 += datetime.timedelta(days=1)
                        diff = t2 - t1
                        hours, remainder = divmod(diff.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        duration_str = f"{hours}h {minutes}m total"

                        if len(recent_activity) < 5:
                            recent_activity.append({
                                "day_num": day_num,
                                "month_short": month_short,
                                "day_name": day_name,
                                "duration": duration_str,
                                "in_time": entry_time[:5],
                                "out_time": exit_time[:5],
                                "is_late": is_late
                            })
                    except Exception as ex:
                        print(f"[ACTIVITY PARSE ERROR] {ex}")

        except Exception as e:
            print(f"[ATTENDANCE FETCH ERROR] {e}")

        employee_data = {
            "emp_id": employee_id,
            "Name": real_name,
            "Email": user_info.get("Email", "Not Provided"),
            "Phone": user_info.get("Phone", "Not Provided"),
            "Job": user_info.get("Job", "Not Specified"),
            "Address": user_info.get("Address", "Not Provided"),
            "Role": db_role,
            "Leave_Status": user_info.get("Leave_Status", "Active"),
            "Photo_Count": photo_count,
            "present_dates": present_dates,
            "late_dates": late_dates,
            "recent_activity": recent_activity
        }
        
        return render_template('employee_detail.html', emp=employee_data)
        
    except Exception as e:
        print(f"[ERROR] Could not load employee detail for {employee_id}: {e}")
        flash("An error occurred while loading employee details.", "danger")
        return redirect(url_for('admin.manage_employees'))

@admin.route('/delete_employee/<name>', methods=['POST'])
def delete_employee(name):
    from models.vector_db import employee_collection
    import os
    
    try:
        results = employee_collection.get(include=["metadatas"])
        all_ids = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        
        ids_to_delete = []
        names_to_delete = []
        
        for i in range(len(all_ids)):
            chroma_id = all_ids[i]
            meta = metadatas[i] if metadatas and i < len(metadatas) and metadatas[i] else {}
            hr_id = meta.get("HR_ID", chroma_id)
            real_name = meta.get("Name", hr_id)
            
            if hr_id == name or chroma_id == name:
                ids_to_delete.append(chroma_id)
                if real_name not in names_to_delete:
                    names_to_delete.append(real_name)
                    
        if ids_to_delete:
            employee_collection.delete(ids=ids_to_delete)
            flash(f"Successfully deleted records for ID {name}.", "success")
        
        # Cleanup: Delete local photos
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                lower_filename = name_without_ext.lower()
                for real_name in names_to_delete:
                    if lower_filename.startswith(f"{real_name.lower()}_") or lower_filename == real_name.lower():
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
    from models.database import collection, universal_registry
    import os
    
    try:
        # 1. Fetch all IDs from Chroma
        results = employee_collection.get()
        all_ids = results.get('ids', [])
        
        # 2. Wipe ChromaDB
        if all_ids:
            employee_collection.delete(ids=all_ids)
            
        # 3. Wipe MongoDB Databases
        collection.delete_many({'Role': {'$regex': '^employee$', '$options': 'i'}})
        universal_registry.delete_many({'Role': {'$regex': '^employee$', '$options': 'i'}})
            
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
    return redirect(url_for('admin.manage_employees'))

@admin.route('/manage_visitors', methods=['GET'])
def manage_visitors():
    from models.vector_db import visitor_collection
    from models.database import universal_registry
    
    try:
        results = visitor_collection.get(include=["documents", "metadatas"])
        visitor_ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        visitor_profiles = []
        seen_ids = set()
        
        for i, vis_id in enumerate(visitor_ids):
            meta = metadatas[i] if metadatas and i < len(metadatas) and metadatas[i] else {}
            real_id = meta.get("Visitor_ID", meta.get("ID", vis_id))
            if str(real_id).startswith("VIS-"):
                parts = str(real_id).split("-")
                if len(parts) >= 2:
                    real_id = parts[1]
                    
            if real_id in seen_ids:
                continue
            seen_ids.add(real_id)
            
            smart_id = f"REGVIS-{real_id}"
            profile = universal_registry.find_one({"_id": smart_id})
            name = documents[i] if documents and i < len(documents) and documents[i] else real_id
            
            if profile:
                profile['num_id'] = real_id
                visitor_profiles.append(profile)
            else:
                visitor_profiles.append({"num_id": real_id, "Name": name, "Phone": "Unknown", "Email": "Unknown"})
                
        total_count = len(visitor_profiles)
                
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
    import os
    
    try:
        results = visitor_collection.get(include=["documents", "metadatas"])
        all_ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        ids_to_delete = []
        visitor_name = str(visitor_id)
        
        for i, vid in enumerate(all_ids):
            meta = metadatas[i] if metadatas and i < len(metadatas) and metadatas[i] else {}
            v_id_meta = meta.get("Visitor_ID", meta.get("ID", vid))
            if str(v_id_meta).startswith("VIS-"):
                v_id_meta = str(v_id_meta).split("-")[1]
                
            if str(vid) == str(visitor_id) or str(v_id_meta) == str(visitor_id) or str(vid).startswith(f"VIS-{visitor_id}-"):
                ids_to_delete.append(vid)
                if documents and i < len(documents) and documents[i]:
                    visitor_name = documents[i]
                    
        if ids_to_delete:
            visitor_collection.delete(ids=ids_to_delete)
        flash(f"Successfully deleted records for ID {visitor_id}.", "success")
        
        # Cleanup: Delete local photos
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if f"_{visitor_id}_" in filename or filename.lower().startswith(f"{visitor_name.lower()}_") or os.path.splitext(filename)[0].lower() == visitor_name.lower():
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
    import os
    
    try:
        # Get the name first before deleting
        results = other_collection.get(ids=[staff_id])
        docs = results.get("documents", [])
        staff_name = docs[0] if docs and len(docs) > 0 and docs[0] else staff_id
        
        other_collection.delete(ids=[staff_id])
        flash(f"Successfully deleted records for ID {staff_id}.", "success")
        
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                lower_filename = name_without_ext.lower()
                if lower_filename.startswith(f"{staff_name.lower()}_") or lower_filename == staff_name.lower():
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
    return redirect(url_for('admin.attendance_timesheet'))

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

def serve_user_face(faces_dir, name, unique_id=""):
    import os
    from flask import send_from_directory, redirect
    from urllib.parse import quote
    
    if os.path.exists(faces_dir):
        # 0. Priority Exact ID match (if ID provided)
        if unique_id:
            clean_id = unique_id.strip().lower()
            for filename in sorted(os.listdir(faces_dir)):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                fname_lower = filename.lower()
                fname_no_ext = os.path.splitext(fname_lower)[0]
                if (f"_{clean_id}_" in fname_lower or 
                    fname_no_ext.endswith(f"_{clean_id}") or
                    fname_no_ext.startswith(f"{clean_id}_") or
                    fname_no_ext == clean_id):
                    return send_from_directory(faces_dir, filename)
                    
        # Legacy Name match fallback
        if name:
            clean_name = name.strip().lower()
            clean_under = clean_name.replace(' ', '_')
            clean_space = clean_name.replace('_', ' ')
            
            # 1. Prefix match (e.g., "An_" matching "An_989_482b22.png")
            for filename in sorted(os.listdir(faces_dir)):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                fname_no_ext = os.path.splitext(filename)[0].lower()
                if (fname_no_ext == clean_name or 
                    fname_no_ext.startswith(clean_name + "_") or 
                    fname_no_ext.startswith(clean_name + " ") or
                    fname_no_ext.startswith(clean_under + "_") or
                    fname_no_ext.startswith(clean_space + "_") or
                    fname_no_ext.startswith(clean_name)):
                    return send_from_directory(faces_dir, filename)
                    
            # 2. Substring match
            for filename in sorted(os.listdir(faces_dir)):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                fname_no_ext = os.path.splitext(filename)[0].lower()
                if clean_name in fname_no_ext or clean_under in fname_no_ext or clean_space in fname_no_ext:
                    return send_from_directory(faces_dir, filename)
                
    # Clean UI Avatars fallback instead of broken SVG
    fallback_name = quote(name if name else (unique_id if unique_id else "User"))
    return redirect(f"https://ui-avatars.com/api/?name={fallback_name}&background=0d6efd&color=fff&size=150")

@admin.route('/employee_image/<name>')
def employee_image(name):
    import os
    from flask import request
    unique_id = request.args.get('id', '').strip()
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'employee_faces')
    return serve_user_face(faces_dir, name, unique_id)

@admin.route('/attendance/visitor', methods=['GET'])
def attendance_visitor():
    from models.database import attendance_log
    import datetime
    from flask import request
    
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
    from flask import request
    unique_id = request.args.get('id', '').strip()
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
    return serve_user_face(faces_dir, name, unique_id)

@admin.route('/attendance/other', methods=['GET'])
def attendance_other():
    from models.database import attendance_log
    import datetime
    from flask import request
    
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
    from flask import request
    unique_id = request.args.get('id', '').strip()
    faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
    return serve_user_face(faces_dir, name, unique_id)

@admin.route('/attendance/timesheet', methods=['GET'])
def attendance_timesheet():
    from models.database import attendance_log, collection
    import datetime
    from flask import request
    
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
    # Create a quick lookup dictionary keyed by ID and Name
    user_lookup = {}
    for user in all_users:
        user_info = {
            "Email": user.get("Email", "N/A"),
            "Job": user.get("Job", "Employee")
        }
        if user.get("HR_ID"):
            user_lookup[str(user.get("HR_ID"))] = user_info
        if user.get("ID"):
            user_lookup[str(user.get("ID"))] = user_info
        name = user.get("Name", "")
        if name:
            user_lookup[name] = user_info
            
    # 3. Build the consolidated Timesheet
    timesheet_data = []
    for log in raw_logs:
        name = log.get("Name", "")
        log_id = log.get("ID", log.get("HR_ID", ""))
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
                
        # Lookup User Info (try by ID first, then Name)
        user_info = user_lookup.get(str(log_id), user_lookup.get(name, {"Email": "Unknown", "Job": "Unknown"}))
        
        timesheet_data.append({
            "ID": log_id,
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
    emp_id = request.form.get('emp_id') or request.form.get('hr_id')
    email = request.form.get('email')
    job = request.form.get('job')
    phone = request.form.get('phone', 'Unknown')
    address = request.form.get('address', 'Unknown')
    leave_status = request.form.get('leave_status', 'Active')
    
    # Build flexible query to match either ID or Name in primary collection
    query_conditions = []
    if emp_id:
        query_conditions.append({"ID": emp_id})
    if name:
        query_conditions.append({"Name": name})
        
    if query_conditions:
        query = {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
        
        # 1. Update Primary MongoDB Collection (used by Inspect Page & Tables)
        collection.update_one(
            query,
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
        
        # 2. Update Shadow Registry if active
        try:
            smart_id = emp_id if emp_id else f"EMP-{name.upper()}"
            universal_registry.update_one(
                {"_id": smart_id},
                {
                    "$set": {
                        "Email": email,
                        "Job": job,
                        "Phone": phone,
                        "Address": address,
                        "Leave_Status": leave_status
                    }
                }
            )
        except Exception as e:
            print(f"[SHADOW DB ERROR] Failed to sync update: {e}")
            
        flash(f"Successfully updated details for {name or emp_id}", "success")
    else:
        flash("Error: Missing Employee Identifier", "danger")
        
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
