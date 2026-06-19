from flask import Blueprint, request, redirect, url_for,render_template,flash,request
from werkzeug.security import generate_password_hash
from models.database import collection, adminlog, securitylog,visitorlogtable,activevisitorstable,reqvistable,rejectedvistable,visitors_status
from datetime import datetime
from flask_bcrypt import Bcrypt
from bson import ObjectId
from collections import defaultdict
from flask import json

admin = Blueprint('admin', __name__)
bcrypt = Bcrypt()

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
       
        if request.form['submit1'] == 'pass':
            Name= request.form['fullname']
            Email=request.form['addemail']
            Phone=request.form['phone']
            Job=request.form['jobtitle']
            Password=request.form['password']
            today = datetime.now()
            hashed_password = generate_password_hash(Password)
            # hashed_password = bcrypt.generate_password_hash(Password).decode('utf-8')
            new_admin = {
                "Name":Name,
                "Email":Email,
                "Phone":Phone,
                "Date":today,
                "Job":Job,
                "Password":hashed_password 

            }
            collection.insert_one(new_admin)
            adminlog.insert_one(new_admin)
        return redirect(url_for('admin.admindash'))
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
    query = {} if status == 'all' else {"Job": status}

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
    
    try:
        results = employee_collection.get()
        employee_names = results.get('ids', [])
        total_count = len(employee_names)
    except Exception as e:
        print(f"[ERROR] Could not fetch employees: {e}")
        employee_names = []
        total_count = 0
        flash("Failed to load employees from database.", "danger")
        
    return render_template('manage_employees.html', employee_names=employee_names, total_count=total_count)

@admin.route('/delete_employee/<name>', methods=['POST'])
def delete_employee(name):
    from models.vector_db import employee_collection
    
    try:
        # Delete from ChromaDB
        employee_collection.delete(ids=[name])
        flash(f"Successfully deleted records for {name}.", "success")
        
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

@admin.route('/manage_visitors', methods=['GET'])
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
        
    return render_template('manage_visitors.html', visitor_names=visitor_names, total_count=total_count)

@admin.route('/delete_visitor/<name>', methods=['POST'])
def delete_visitor(name):
    from models.vector_db import visitor_collection
    
    try:
        # Delete from ChromaDB
        visitor_collection.delete(ids=[name])
        flash(f"Successfully deleted records for {name}.", "success")
        
        # Cleanup: Delete local photo
        import os
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visitor_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                if name_without_ext.lower() == name.lower():
                    try:
                        os.remove(os.path.join(faces_dir, filename))
                    except Exception:
                        pass
                
    except Exception as e:
        flash(f"Error deleting {name}: {e}", "danger")
        
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
        
    return render_template('manage_other.html', external_staff=external_staff, total_count=total_count)

@admin.route('/delete_other/<name>', methods=['POST'])
def delete_other(name):
    from models.vector_db import other_collection
    
    try:
        other_collection.delete(ids=[name])
        flash(f"Successfully deleted records for {name}.", "success")
        
        import os
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'external_faces')
        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                name_without_ext = os.path.splitext(filename)[0]
                if name_without_ext.lower() == name.lower():
                    try:
                        os.remove(os.path.join(faces_dir, filename))
                    except Exception:
                        pass
                
    except Exception as e:
        flash(f"Error deleting {name}: {e}", "danger")
        
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
