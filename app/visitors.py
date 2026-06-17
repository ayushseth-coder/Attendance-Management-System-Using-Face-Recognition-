from flask import Blueprint, redirect, url_for, request, render_template, flash
from models.database import reqvistable, visitorlogtable, activevisitorstable, rejectedvistable,otp_send, visitors_status
from app.camera_manager import release_camera
import datetime,os

visitor = Blueprint('visitors', __name__)


@visitor.route('/visitor1', methods=['GET', 'POST'])
def visitor1():
    global approvedby, dobee, dataobject1,pan_data
    
    if request.method == 'POST':
        if request.form['submit'] == 'pass':
            name = request.form['name']
            father = request.form['father']
            dob = request.form['dob']
            gender = request.form['gender']
            uid = request.form['uid']
            date = request.form['Date']
            purpose = request.form['Purpose']
            email = request.form['Email']
            phone = request.form['phone']
            apprv = request.form['Approvedby']
            card = request.form['card']
            shot_filename = request.form.get('shot_filename', '')
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
                "phone": phone,
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
    shot_filename = element1.get('shot_filename')
    if shot_filename:
        try:
            from deepface import DeepFace
            from models.vector_db import visitor_collection
            import os
            import shutil
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_dir, 'static', 'shots', shot_filename)
            
            # Create the permanent physical folder for visitor faces
            visitor_faces_dir = os.path.join(base_dir, 'visitor_faces')
            os.makedirs(visitor_faces_dir, exist_ok=True)
            
            if os.path.exists(img_path):
                visitor_name = element1['Name']
                permanent_img_path = os.path.join(visitor_faces_dir, f"{visitor_name}.png")
                
                # Copy the temporary shot to the permanent database folder
                shutil.copy2(img_path, permanent_img_path)
                
                print(f"[INFO] Extracting vector for Regular Visitor: {visitor_name}")
                # enforce_detection=False here because we already captured it via OCR fallback where they might not be perfectly centered.
                # representations = DeepFace.represent(img_path=permanent_img_path, model_name="Facenet", enforce_detection=False)
                representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=False)
                
                if representations and len(representations) > 0:
                    embedding = representations[0]["embedding"]
                    
                    if visitor_collection is not None:
                        visitor_collection.upsert(
                            embeddings=[embedding],
                            documents=[visitor_name],
                            ids=[visitor_name]
                        )
                        print(f"[SUCCESS] Regular Visitor {visitor_name} permanently enrolled in ChromaDB!")
        except Exception as e:
            print(f"[ERROR] Failed to enroll Regular Visitor in ChromaDB: {e}")

    # 2. Standard Accept Logic
    reqvistable.delete_one({"UID": uid})
    visitorlogtable.insert_one(element1)
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
        return redirect(url_for('admin.admindash'))

    shot_filename = element1.get('shot_filename')
    if shot_filename:
        try:
            from deepface import DeepFace
            from models.vector_db import employee_collection
            import os
            import shutil
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_dir, 'static', 'shots', shot_filename)
            
            # Create permanent folder for employee faces if it doesn't exist
            employee_faces_dir = os.path.join(base_dir, 'employee_faces')
            os.makedirs(employee_faces_dir, exist_ok=True)
            
            if os.path.exists(img_path):
                # Standardize employee names (often lowercase or capitalized consistently)
                employee_name = element1['Name'].strip().capitalize() 
                permanent_img_path = os.path.join(employee_faces_dir, f"{employee_name}.png")
                
                # Copy the temporary shot to the permanent database folder
                shutil.copy2(img_path, permanent_img_path)
                
                print(f"[INFO] Extracting vector for New Employee: {employee_name}")
                # representations = DeepFace.represent(img_path=permanent_img_path, model_name="Facenet", enforce_detection=False)
                representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=False)
                
                if representations and len(representations) > 0:
                    embedding = representations[0]["embedding"]
                    
                    if employee_collection is not None:
                        employee_collection.upsert(
                            embeddings=[embedding],
                            documents=[employee_name],
                            ids=[employee_name]
                        )
                        print(f"[SUCCESS] Employee {employee_name} permanently enrolled in ChromaDB!")
        except Exception as e:
            print(f"[ERROR] Failed to enroll Employee in ChromaDB: {e}")

    # Remove from pending requests
    reqvistable.delete_one({"UID": uid})

    # Note: We do not add employees to visitorlogtable or activevisitorstable, 
    # because they are employees, not visitors.
    status = 'Enrolled as Employee' 
    myquery = visitors_status.find_one({"UID": uid})
    if myquery:
        visitors_status.update_one(myquery, {"$set": {"status": status}})

    return redirect(url_for('admin.admindash'))

@visitor.route('/enroll_external/<uid>', methods=['GET'])
def enroll_external(uid):
    element1 = reqvistable.find_one({"UID": uid})
    if not element1:
        return redirect(url_for('admin.admindash'))

    shot_filename = element1.get('shot_filename')
    role = element1.get('Registration_Role', 'External Staff')
    
    if shot_filename:
        try:
            from deepface import DeepFace
            from models.vector_db import other_collection
            import os
            import shutil
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_dir, 'static', 'shots', shot_filename)
            
            # Create permanent folder for external faces if it doesn't exist
            external_faces_dir = os.path.join(base_dir, 'external_faces')
            os.makedirs(external_faces_dir, exist_ok=True)
            
            if os.path.exists(img_path):
                external_name = element1['Name'].strip().title() 
                permanent_img_path = os.path.join(external_faces_dir, f"{external_name}.png")
                
                shutil.copy2(img_path, permanent_img_path)
                
                print(f"[INFO] Extracting vector for External Staff: {external_name} ({role})")
                # representations = DeepFace.represent(img_path=permanent_img_path, model_name="Facenet", enforce_detection=False)
                representations = DeepFace.represent(img_path=permanent_img_path, model_name="ArcFace", enforce_detection=False)
                
                if representations and len(representations) > 0:
                    embedding = representations[0]["embedding"]
                    
                    if other_collection is not None:
                        other_collection.upsert(
                            embeddings=[embedding],
                            documents=[external_name],
                            metadatas=[{"Role": role}],
                            ids=[external_name]
                        )
                        print(f"[SUCCESS] {role} {external_name} permanently enrolled in ChromaDB!")
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
  
    visitorlogtable.insert_one(element1)
    activevisitorstable.insert_one(element1)
    status = 'accepted' 
    myquery = visitors_status.find_one({"UID": uid})

    visitors_status.update_one(myquery, {"$set": {"status": status}})


    return redirect(url_for('admin.admindash'))


@visitor.route('/rejectvis/<uid>', methods=['POST','GET'])
def rejectvis(uid):
    element2 = reqvistable.find_one({"UID": uid})
    reqvistable.delete_one({"UID": uid})
    rejectedvistable.insert_one(element2)
    
    visitors_status.update_one({"UID": uid}, {"$set": {"status": "rejected"}})
    
    return redirect(url_for('admin.admindash'))



