from flask import Blueprint, redirect, url_for, request, render_template
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
                "shot_filename": shot_filename
            }
            
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
            
            img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'shots', shot_filename)
            
            if os.path.exists(img_path):
                print(f"[INFO] Extracting vector for Regular Visitor: {element1['Name']}")
                # enforce_detection=False here because we already captured it via OCR fallback where they might not be perfectly centered.
                representations = DeepFace.represent(img_path=img_path, model_name="Facenet", enforce_detection=False)
                
                if representations and len(representations) > 0:
                    embedding = representations[0]["embedding"]
                    visitor_name = element1['Name']
                    
                    if visitor_collection is not None:
                        visitor_collection.add(
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



