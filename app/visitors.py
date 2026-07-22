from flask import Blueprint, redirect, url_for, request, render_template, flash, session
from models.database import reqvistable, visitorlogtable, activevisitorstable, rejectedvistable,otp_send, visitors_status
from app.camera_manager import release_camera
import datetime,os

visitor = Blueprint('visitors', __name__)

@visitor.before_request
def require_staff_login():
    if request.endpoint and 'static' in request.endpoint:
        return
    role = session.get('role')
    if not session.get('logged_in') or role not in ['admin', 'security']:
        flash("You do not have permission to access visitor actions.", "danger")
        return redirect(url_for('auth.login'))


@visitor.route('/visitor1', methods=['GET', 'POST'])
def visitor1():
    global approvedby, dobee, dataobject1,pan_data
    
    if request.method == 'POST':
        if request.form['submit'] == 'pass':
            name = request.form.get('name', 'N/A')
            father = request.form.get('father', 'N/A')
            dob = request.form.get('dob', 'N/A')
            gender = request.form.get('gender', 'N/A')
            uid = request.form.get('uid', 'N/A')
            date = request.form.get('Date', '')
            purpose = request.form.get('Purpose', 'N/A')
            email = request.form.get('Email', 'N/A')
            phone = request.form.get('phone', 'N/A')
            apprv = request.form.get('Approvedby', 'N/A')
            card = request.form.get('card', 'N/A')
            shot_filename = request.form.get('shot_filename', '')
            
            # Strict Validation: Prevent submitting the form if no photo was captured
            if not shot_filename:
                flash("Error: No photo was captured! You must have a valid facial scan to enroll.", "danger")
                return redirect(request.referrer or url_for('security.securitydash'))

            registration_role = request.form.get('Registration_Role', 'Visitor')
            role_type = request.form.get('role_type', 'visitor')
            is_delivery = (role_type == 'delivery')

            dataobject1 = {
                "Name": name,
                "Gender": gender,
                "Card": card,
                "UID": uid,
                "Date": date,
                "Purpose": purpose,
                "Email": email,
                "Phone": phone,
                "Approvedby": apprv,
                "Exittime": "",
                "status":"",
                "shot_filename": shot_filename,
                "Registration_Role": registration_role
            }
            
            if is_delivery:
                from models.database import other_logs_table
                dataobject1["status"] = "Quick Log"
                other_logs_table.insert_one(dataobject1)
                flash("Delivery/Maintenance Log saved successfully!", "success")
                return redirect(url_for('security.security_home'))
            else:
                reqvistable.insert_one(dataobject1)
            visitors_status.insert_one(dataobject1)
            dobee = 1
            
        return redirect(url_for('security.securitydash'))

   
    # return render_template('security_dashboard.html',data=pan_data)


@visitor.route('/deletevis/<uid>', methods=['POST', 'GET'])
def deletevis(uid):
    global approvedby
    activevisitorstable.delete_one({"UID": uid})
    now1 = datetime.datetime.now()
    dt_string = now1.strftime("%d/%m/%Y %H:%M:%S")
    myquery = {"UID": uid}
    newvalues = {"$set": {"Exittime": dt_string}}
    visitorlogtable.update_one(myquery, newvalues)
    return redirect(url_for('security.securitydash'))

@visitor.route('/accept_regular/<uid>', methods=['GET'])
def accept_regular(uid):
    element1 = reqvistable.find_one({"UID": uid})
    if not element1:
        return redirect(url_for('admin.admindash'))

    # 1. Save Vector to ChromaDB
    shot_filenames = element1.get('shot_filename')
    if shot_filenames:
        try:
            from deepface import DeepFace
            from models.vector_db import visitor_collection
            import os
            import shutil
            import uuid
            import cv2
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            visitor_faces_dir = os.path.join(base_dir, 'visitor_faces')
            os.makedirs(visitor_faces_dir, exist_ok=True)
            
            for shot_filename in shot_filenames.split(','):
                shot_filename = shot_filename.strip()
                if not shot_filename: continue
                img_path = os.path.join(base_dir, 'static', 'shots', shot_filename)
                
                if os.path.exists(img_path):
                    visitor_name = element1['Name']
                    random_suffix = str(uuid.uuid4())[:6]
                    permanent_img_path = os.path.join(visitor_faces_dir, f"{visitor_name}_{random_suffix}.png")
                    shutil.copy2(img_path, permanent_img_path)
                    
                    # Apply CLAHE
                    img = cv2.imread(permanent_img_path)
                    if img is not None:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                        enhanced_gray = clahe.apply(gray)
                        enhanced_img = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
                        cv2.imwrite(permanent_img_path, enhanced_img)
                        
                    print(f"[INFO] Extracting vector for Regular Visitor (Multi-Shot): {visitor_name}")
                    # --- Liveness Check (Anti-Spoofing) ---
                    from models.anti_spoofing import liveness_detector
                    is_real, score = liveness_detector.check_liveness(permanent_img_path)
                    if is_real == "TooClose":
                        print("[WARNING] Face Too Close on Enrollment Frame!")
                        continue
                    elif not is_real:
                        print(f"[WARNING] Spoofing Detected on Enrollment Frame! (Score: {score:.2f})")
                        continue # Skip saving this fake image to DB
                        
                    print(f"[INFO] Extracting vector for Regular Visitor (Multi-Shot): {visitor_name}")
                    representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=False)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        if visitor_collection is not None:
                            import random
                            num_id = str(random.randint(100000, 999999))
                            visitor_collection.upsert(
                                embeddings=[embedding],
                                documents=[visitor_name],
                                ids=[num_id]
                            )
            print(f"[SUCCESS] Regular Visitor {element1['Name']} permanently enrolled (Multi-Shot) in ChromaDB!")
        except Exception as e:
            print(f"[ERROR] Failed to enroll Regular Visitor in ChromaDB: {e}")

    # 2. Standard Accept Logic
    reqvistable.delete_one({"UID": uid})
    
    # Strip _id to avoid DuplicateKeyError across collections
    if "_id" in element1:
        del element1["_id"]
    visitorlogtable.insert_one(element1)
    
    # Strip newly added _id before next insert
    if "_id" in element1:
        del element1["_id"]
    activevisitorstable.insert_one(element1)
    status = 'accepted' 
    myquery = visitors_status.find_one({"UID": uid})
    if myquery:
        visitors_status.update_one(myquery, {"$set": {"status": status}})

    return redirect(url_for('admin.admindash'))

@visitor.route('/enroll_employee/<uid>', methods=['GET'])
def enroll_employee(uid):
    element1 = reqvistable.find_one({"UID": uid})
    if not element1:
        flash("Pending request not found.", "danger")
        return redirect(url_for('admin.admindash'))
        
    return render_template('review_employee_enrollment.html', req=element1)


@visitor.route('/process_employee_enrollment/<uid>', methods=['POST'])
def process_employee_enrollment(uid):
    element1 = reqvistable.find_one({"UID": uid})
    if not element1:
        flash("Pending request not found.", "danger")
        return redirect(url_for('admin.admindash'))
        
    name = request.form.get('name')
    email = request.form.get('email', 'Unknown')
    
    # Pre-check: Ensure the email isn't already registered in MongoDB before running AI extraction
    from models.database import collection
    if collection.find_one({"Email": email}):
        flash(f"Error: The email {email} is already registered. Please use a different email or delete the existing record.", "danger")
        return redirect(request.referrer or url_for('admin.admindash'))

    phone = request.form.get('phone', 'Unknown')
    gender = request.form.get('gender', 'Unknown')
    job = request.form.get('role', 'Unknown')
    
    shot_filename = element1.get('shot_filename')
    if shot_filename:
        try:
            from deepface import DeepFace
            from models.vector_db import employee_collection
            from models.database import collection, universal_registry
            import os
            import shutil
            import uuid
            import re
            import cv2
            import datetime
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            employee_faces_dir = os.path.join(base_dir, 'employee_faces')
            os.makedirs(employee_faces_dir, exist_ok=True)
            
            # --- COMBINED MULTI-SHOT AND DB LOGIC ---
            employee_name = name.strip().capitalize() 
            
            match = re.match(r"([A-Za-z]+)[_-]?(\d*)", employee_name)
            if match:
                clean_name = match.group(1).capitalize()
                extracted_id = match.group(2)
            else:
                clean_name = employee_name.capitalize()
                extracted_id = ""
                
            base_hr_id = f"EMP-{extracted_id}" if extracted_id else f"EMP-{clean_name.upper()}"
            
            for shot in shot_filename.split(','):
                shot = shot.strip()
                if not shot: continue
                img_path = os.path.join(base_dir, 'static', 'shots', shot)
                
                if os.path.exists(img_path):
                    random_suffix = str(uuid.uuid4())[:6]
                    permanent_img_path = os.path.join(employee_faces_dir, f"{employee_name}_{random_suffix}.png")
                    shutil.copy2(img_path, permanent_img_path)
                    
                    # --- Liveness Check (Anti-Spoofing) MUST BE DONE ON ORIGINAL COLOR IMAGE ---
                    from models.anti_spoofing import liveness_detector
                    is_real, score = liveness_detector.check_liveness(permanent_img_path)
                    if is_real == "TooClose":
                        print("[WARNING] Face Too Close on Enrollment Frame!")
                        os.remove(permanent_img_path)
                        continue
                    elif not is_real:
                        print(f"[WARNING] Spoofing Detected on Enrollment Frame! (Score: {score:.2f})")
                        os.remove(permanent_img_path)
                        continue # Skip saving this fake image to DB
                        
                    # Apply CLAHE (After liveness check, because CLAHE makes it grayscale causing Saturation=0)
                    img = cv2.imread(permanent_img_path)
                    if img is not None:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                        enhanced_gray = clahe.apply(gray)
                        enhanced_img = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
                        cv2.imwrite(permanent_img_path, enhanced_img)
                        
                    print(f"[INFO] Extracting vector for Employee Burst Image: {employee_name}")
                        
                    representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=True)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        if employee_collection is not None:
                            chroma_id = f"{base_hr_id}-{str(uuid.uuid4())[:6].upper()}"
                            
                            employee_collection.upsert(
                                embeddings=[embedding],
                                ids=[chroma_id],
                                metadatas=[{"path": permanent_img_path, "Name": clean_name, "HR_ID": base_hr_id}]
                            )
            
            print(f"[SUCCESS] Employee {employee_name} permanently enrolled (Multi-Shot) in ChromaDB!")
            
            # Save Data to MongoDB Collection
            collection.insert_one({
                "Name": name,
                "Email": email,
                "Phone": phone,
                "Gender": gender,
                "Job": job,
                "Address": "Unknown",
                "Leave_Status": "Active",
                "Password": "",
                "Date": datetime.datetime.now()
            })
            
            # Save Data to Universal Registry (Shadow DB)
            universal_registry.update_one(
                {"_id": base_hr_id},
                {
                    "$set": {
                        "Date": datetime.datetime.now().strftime('%Y-%m-%d'),
                        "Email": email,
                        "Phone": phone,
                        "Gender": gender,
                        "Job": job,
                        "Address": "Unknown",
                        "Leave_Status": "Active"
                    },
                    "$setOnInsert": {
                        "Name": clean_name,
                        "Role": "Employee",
                        "Visitor_Type": "Regular"
                    }
                },
                upsert=True
            )
            
            print(f"[SUCCESS] Employee {employee_name} fully onboarded via Admin Review!")
            flash(f"Successfully onboarded employee {name}.", "success")
        except Exception as e:
            print(f"[ERROR] Failed to enroll Employee: {e}")
            flash(f"Failed to onboard employee: {e}", "danger")

    # Remove from pending requests
    reqvistable.delete_one({"UID": uid})
    
    status = 'Enrolled as Employee' 
    myquery = visitors_status.find_one({"UID": uid})
    if myquery:
        visitors_status.update_one(myquery, {"$set": {"status": status}})

    return redirect(url_for('admin.manage_employees'))

@visitor.route('/enroll_external/<uid>', methods=['GET'])
def enroll_external(uid):
    element1 = reqvistable.find_one({"UID": uid})
    if not element1:
        return redirect(url_for('admin.admindash'))

    shot_filenames = element1.get('shot_filename')
    role = element1.get('Registration_Role', 'External Staff')
    
    if shot_filenames:
        try:
            from deepface import DeepFace
            from models.vector_db import other_collection
            import os
            import shutil
            import uuid
            import cv2
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            external_faces_dir = os.path.join(base_dir, 'external_faces')
            os.makedirs(external_faces_dir, exist_ok=True)
            
            for shot_filename in shot_filenames.split(','):
                shot_filename = shot_filename.strip()
                if not shot_filename: continue
                img_path = os.path.join(base_dir, 'static', 'shots', shot_filename)
                
                if os.path.exists(img_path):
                    external_name = element1['Name'].strip().title()
                    random_suffix = str(uuid.uuid4())[:6]
                    permanent_img_path = os.path.join(external_faces_dir, f"{external_name}_{random_suffix}.png")
                    shutil.copy2(img_path, permanent_img_path)
                    
                    # Apply CLAHE
                    img = cv2.imread(permanent_img_path)
                    if img is not None:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                        enhanced_gray = clahe.apply(gray)
                        enhanced_img = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
                        cv2.imwrite(permanent_img_path, enhanced_img)
                        
                    print(f"[INFO] Extracting vector for External Staff (Multi-Shot): {external_name} ({role})")
                    # --- Liveness Check (Anti-Spoofing) ---
                    from models.anti_spoofing import liveness_detector
                    is_real, score = liveness_detector.check_liveness(permanent_img_path)
                    if not is_real:
                        print(f"[WARNING] Spoofing Detected on Enrollment Frame! (Score: {score:.2f})")
                        continue # Skip saving this fake image to DB
                        
                    print(f"[INFO] Extracting vector for Regular Visitor (Multi-Shot): {visitor_name}")
                    representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=False)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        if other_collection is not None:
                            import random
                            num_id = str(random.randint(100000, 999999))
                            other_collection.upsert(
                                embeddings=[embedding],
                                documents=[external_name],
                                metadatas=[{"Role": role}],
                                ids=[num_id]
                            )
            print(f"[SUCCESS] {role} {element1['Name']} permanently enrolled (Multi-Shot) in ChromaDB!")
        except Exception as e:
            print(f"[ERROR] Failed to enroll External Staff in ChromaDB: {e}")

    reqvistable.delete_one({"UID": uid})

    status = f'Enrolled as {role}' 
    myquery = visitors_status.find_one({"UID": uid})
    if myquery:
        visitors_status.update_one(myquery, {"$set": {"status": status}})

    return redirect(url_for('admin.admindash'))

@visitor.route('/acceptvis/<uid>', methods=['POST', 'GET'])
def acceptvis(uid):
    element1 = reqvistable.find_one({"UID": uid})
    reqvistable.delete_one({"UID": uid})
  
    if "_id" in element1:
        del element1["_id"]
    visitorlogtable.insert_one(element1)
    
    if "_id" in element1:
        del element1["_id"]
    activevisitorstable.insert_one(element1)
    status = 'accepted' 
    myquery = visitors_status.find_one({"UID": uid})

    visitors_status.update_one(myquery, {"$set": {"status": status}})


    return redirect(url_for('admin.admindash'))


@visitor.route('/rejectvis/<uid>', methods=['POST','GET'])
def rejectvis(uid):
    element2 = reqvistable.find_one({"UID": uid})
    reqvistable.delete_one({"UID": uid})
    if "_id" in element2:
        del element2["_id"]
    rejectedvistable.insert_one(element2)
    
    visitors_status.update_one({"UID": uid}, {"$set": {"status": "rejected"}})
    
    return redirect(url_for('admin.admindash'))



