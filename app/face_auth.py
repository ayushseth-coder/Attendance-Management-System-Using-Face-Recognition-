from flask import Blueprint, render_template, request, Response, redirect, url_for
import cv2
import datetime
import os
import time
from app.camera_manager import get_camera, release_camera
from models.database import attendance_log
from app.image_processing import captured_data, captured_image  # Import global to share state with OCR fallback

face_auth = Blueprint('face_auth', __name__)

global face_match_data
face_match_data = None

# --- PERFORMANCE OPTIMIZATION: PRE-LOAD AI MODEL ---
try:
    from deepface import DeepFace
    print("[INFO] Pre-loading Facenet model weights into RAM...")
    DeepFace.build_model("Facenet")
    deepface_available = True
    print("[SUCCESS] Facenet model ready.")
except Exception as e:
    deepface_available = False
    print(f"[WARNING] DeepFace import failed: {e}. Face auth will fail.")
# ---------------------------------------------------

def gen_face_frames():
    global face_match_data
    import app.image_processing as imp # Access the global state for fallback
    imp.captured_data = None
    imp.captured_image = None
    face_match_data = None
    
    camera = get_camera()
    start_time = time.time()
    countdown_duration = 5.0  # reduced to 5 seconds

    try:
        while True:
            success, frame = camera.read()
            if not success:
                time.sleep(0.1)
                continue

            elapsed_time = time.time() - start_time

            if elapsed_time >= countdown_duration and imp.captured_image is None:
                now = datetime.datetime.now()
                os.makedirs('static/shots', exist_ok=True)
                filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}.png")
                cv2.imwrite(filename, frame)
                imp.captured_image = filename
                print(f"[INFO] Face captured and saved to {filename}")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        release_camera()


@face_auth.route('/select_role')
def select_role():
    return render_template('select_role.html')

@face_auth.route('/face_login')
def face_login():
    return render_template('face_camera.html')

@face_auth.route('/face_video_feed')
def face_video_feed():
    return Response(gen_face_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@face_auth.route('/face_result')
def face_result():
    global face_match_data
    import app.image_processing as imp
    from models.vector_db import employee_collection

    match_found = False
    
    if imp.captured_image and deepface_available:
        print(f"[INFO] Processing {imp.captured_image} for Face Match using Facenet...")
        try:
            # --- OLD POC CODE (Preserved for Reference) ---
            # dfs = DeepFace.find(img_path=imp.captured_image, db_path='employee_faces/', enforce_detection=False, silent=True)
            # if len(dfs) > 0 and not dfs[0].empty:
            #     matched_employee_path = dfs[0].iloc[0]['identity']
            #     employee_name = os.path.basename(matched_employee_path).split('.')[0].capitalize()
            #     now = datetime.datetime.now()
            #     face_match_data = {"Name": employee_name, "Date": now.strftime('%Y-%m-%d %H:%M:%S'), "Status": "Present"}
            #     attendance_log.insert_one(face_match_data)
            #     match_found = True
            # ----------------------------------------------

            # 1. Extract vector of captured face using the lightweight Facenet model
            # SECURITY UPDATE: enforce_detection=True ensures that if an arm covers the face, it rejects the photo!
            representations = DeepFace.represent(img_path=imp.captured_image, model_name="Facenet", enforce_detection=True)
            
            if representations and len(representations) > 0:
                embedding = representations[0]["embedding"]
                
                # 2. Query ChromaDB for closest match
                if employee_collection is not None and employee_collection.count() > 0:
                    results = employee_collection.query(
                        query_embeddings=[embedding],
                        n_results=1
                    )
                    
                    # 3. Check distance (cosine threshold for Facenet)
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        # SECURITY UPDATE: Tightened threshold from 0.40 to 0.30 for Enterprise Scalability
                        # This prevents False Positives when the database contains hundreds of faces.
                        if distance < 0.30:  # Highly strict match
                            employee_name = results['ids'][0][0].capitalize()
                            now = datetime.datetime.now()
                            face_match_data = {"Name": employee_name, "Date": now.strftime('%Y-%m-%d %H:%M:%S'), "Status": "Present"}
                            attendance_log.insert_one(face_match_data)
                            match_found = True
                            print(f"[SUCCESS] Face matched with {employee_name} (Distance: {distance})")
                        else:
                            print(f"[INFO] Closest match distance ({distance}) exceeded threshold. Treating as Visitor.")
                else:
                    print("[WARNING] ChromaDB collection is empty or not loaded.")
        except ValueError:
            print("[INFO] No clear face detected in the image (enforce_detection triggered). Treating as Visitor.")
        except Exception as e:
            print(f"[ERROR] Face Recognition failed: {e}")

    if match_found:
        shot_filename = os.path.basename(imp.captured_image) if imp.captured_image else None
        return render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)
    else:
        print("[INFO] Face not recognized. Falling back to Visitor OCR pipeline.")
        return redirect(url_for('image_processing.show_captured'))

@face_auth.route('/visitor_auth')
def visitor_auth():
    return render_template('visitor_camera.html')

@face_auth.route('/visitor_result')
def visitor_result():
    global face_match_data
    import app.image_processing as imp
    from models.vector_db import visitor_collection
    
    match_found = False
    
    if imp.captured_image and deepface_available:
        print(f"[INFO] Processing {imp.captured_image} for Visitor Pre-Check using Facenet...")
        try:
            representations = DeepFace.represent(img_path=imp.captured_image, model_name="Facenet", enforce_detection=True)
            
            if representations and len(representations) > 0:
                embedding = representations[0]["embedding"]
                
                if visitor_collection is not None and visitor_collection.count() > 0:
                    results = visitor_collection.query(
                        query_embeddings=[embedding],
                        n_results=1
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        # Same strict threshold for Regular Visitors
                        if distance < 0.30: 
                            visitor_name = results['ids'][0][0].capitalize()
                            now = datetime.datetime.now()
                            face_match_data = {"Name": visitor_name, "Date": now.strftime('%Y-%m-%d %H:%M:%S'), "Status": "Regular Visitor"}
                            attendance_log.insert_one(face_match_data)
                            match_found = True
                            print(f"[SUCCESS] Regular Visitor matched with {visitor_name} (Distance: {distance})")
                        else:
                            print(f"[INFO] Closest match distance ({distance}) exceeded threshold. Treating as New Visitor.")
                else:
                    print("[WARNING] visitor_faces collection is empty.")
        except ValueError:
            print("[INFO] No clear face detected. Treating as New Visitor.")
        except Exception as e:
            print(f"[ERROR] Visitor Recognition failed: {e}")

    if match_found:
        shot_filename = os.path.basename(imp.captured_image) if imp.captured_image else None
        # Reuse the success template for Regular Visitors
        return render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)
    else:
        print("[INFO] Unknown Visitor. Falling back to OCR Form Registration.")
        return redirect(url_for('image_processing.show_captured'))
