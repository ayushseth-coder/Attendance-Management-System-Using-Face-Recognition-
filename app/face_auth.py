from flask import Blueprint, render_template, request, Response, redirect, url_for
import cv2
import datetime
import os
import time
from app.camera_manager import get_camera, release_camera
from models.database import attendance_log
from app.extensions import limiter

face_auth = Blueprint('face_auth', __name__)

global face_match_data
face_match_data = None

# --- PERFORMANCE OPTIMIZATION: PRE-LOAD AI MODEL ---
try:
    from deepface import DeepFace
    # print("[INFO] Pre-loading Facenet model weights into RAM...")
    # DeepFace.build_model("Facenet")
    print("[INFO] Pre-loading ArcFace model weights into RAM...")
    DeepFace.build_model("ArcFace")
    deepface_available = True
    # print("[SUCCESS] Facenet model ready.")
    print("[SUCCESS] ArcFace model ready.")
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
@limiter.limit("6 per minute")
def face_result():
    global face_match_data
    import app.image_processing as imp
    from models.vector_db import employee_collection
    import os
    import datetime
    import cv2
    from app.camera_manager import get_camera

    match_found = False
    
    if not imp.captured_image:
        camera = get_camera()
        success, frame = camera.read()
        if success:
            now = datetime.datetime.now()
            os.makedirs('static/shots', exist_ok=True)
            filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(filename, frame)
            imp.captured_image = filename
            print(f"[INFO] Fallback capture succeeded for Employee: {filename}")
            
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
            # representations = DeepFace.represent(img_path=imp.captured_image, model_name="Facenet", enforce_detection=True)
            import time
            start_time = time.time()
            representations = DeepFace.represent(img_path=imp.captured_image, model_name="ArcFace", enforce_detection=True, detector_backend="opencv")
            latency = (time.time() - start_time) * 1000
            print(f"[BENCHMARK] ArcFace Extraction Latency (Employee): {latency:.2f} ms")
            
            if representations and len(representations) > 0:
                embedding = representations[0]["embedding"]
                
                # 2. Query ChromaDB for closest match
                if employee_collection is not None and employee_collection.count() > 0:
                    results = employee_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["distances", "metadatas", "documents"]
                    )
                    
                    # 3. Check distance (cosine threshold for Facenet)
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        # SECURITY UPDATE: Adjusted ArcFace threshold to 0.55 based on user testing
                        # This balances security with correct matching in varying lighting conditions.
                        if distance < 0.55:  # Standard Threshold
                            chroma_id = results['ids'][0][0]
                            employee_name = results['metadatas'][0][0].get('Name', chroma_id).capitalize() if results.get('metadatas') and results['metadatas'][0] else chroma_id.capitalize()
                            hr_id = results['metadatas'][0][0].get('HR_ID') if results.get('metadatas') and results['metadatas'][0] else None
                            
                            now = datetime.datetime.now()
                            today_str = now.strftime('%Y-%m-%d')
                            time_str = now.strftime('%H:%M:%S')
                            
                            # Check if they already scanned in today
                            existing_log = attendance_log.find_one({
                                "Name": employee_name,
                                "Date": {"$regex": f"^{today_str}"}
                            })
                            
                            if existing_log:
                                # They already scanned in today, so this scan must be an EXIT
                                attendance_log.update_one(
                                    {"_id": existing_log["_id"]},
                                    {"$set": {"ExitTime": time_str}}
                                )
                                face_match_data = existing_log
                                face_match_data["ExitTime"] = time_str
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(employee_name, "Employee", existing_log.get("Date").split(" ")[1], time_str, hr_id=hr_id)
                            else:
                                # First time scanning today (ENTRY)
                                face_match_data = {
                                    "Name": employee_name, 
                                    "Date": f"{today_str} {time_str}",
                                    "Status": "Present",
                                    "ExitTime": None
                                }
                                attendance_log.insert_one(face_match_data)
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(employee_name, "Employee", time_str, None, hr_id=hr_id)
                                
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
        
        # AUTO-DELETE LOGIC: Delete the file after 5 seconds to free up storage
        # 5 seconds gives the frontend HTML enough time to download and render the image!
        if imp.captured_image:
            import threading
            def delete_file_later(filepath, delay=5):
                import time, os
                time.sleep(delay)
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
            threading.Thread(target=delete_file_later, args=(imp.captured_image,)).start()
            
        return render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)
    else:
        print("[INFO] Face not recognized. Falling back to Employee OCR pipeline.")
        return redirect(url_for('image_processing.show_captured', role_type='employee'))

@face_auth.route('/visitor_auth')
def visitor_auth():
    return render_template('visitor_camera.html')

@face_auth.route('/visitor_result')
@limiter.limit("6 per minute")
def visitor_result():
    global face_match_data
    import app.image_processing as imp
    from models.vector_db import visitor_collection
    import os
    import datetime
    import cv2
    from app.camera_manager import get_camera
    
    match_found = False
    
    if not imp.captured_image:
        camera = get_camera()
        success, frame = camera.read()
        if success:
            now = datetime.datetime.now()
            os.makedirs('static/shots', exist_ok=True)
            filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(filename, frame)
            imp.captured_image = filename
            print(f"[INFO] Fallback capture succeeded for Visitor: {filename}")
            
    if imp.captured_image and deepface_available:
        # print(f"[INFO] Processing {imp.captured_image} for Visitor Pre-Check using Facenet...")
        print(f"[INFO] Processing {imp.captured_image} for Visitor Pre-Check using ArcFace...")
        try:
            # representations = DeepFace.represent(img_path=imp.captured_image, model_name="Facenet", enforce_detection=True)
            import time
            start_time = time.time()
            representations = DeepFace.represent(img_path=imp.captured_image, model_name="ArcFace", enforce_detection=True, detector_backend="opencv")
            latency = (time.time() - start_time) * 1000
            print(f"[BENCHMARK] ArcFace Extraction Latency (Visitor): {latency:.2f} ms")
            
            if representations and len(representations) > 0:
                embedding = representations[0]["embedding"]
                
                if visitor_collection is not None and visitor_collection.count() > 0:
                    results = visitor_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["documents", "distances"]
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        if distance < 0.55: 
                            visitor_id = results['ids'][0][0]
                            visitor_name = results['documents'][0][0].capitalize() if results.get('documents') and results['documents'][0] else visitor_id
                            now = datetime.datetime.now()
                            today_str = now.strftime('%Y-%m-%d')
                            time_str = now.strftime('%H:%M:%S')
                            
                            existing_log = attendance_log.find_one({
                                "Name": visitor_name,
                                "Date": {"$regex": f"^{today_str}"}
                            })
                            
                            if existing_log:
                                attendance_log.update_one(
                                    {"_id": existing_log["_id"]},
                                    {"$set": {"ExitTime": time_str}}
                                )
                                face_match_data = existing_log
                                face_match_data["ExitTime"] = time_str
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(visitor_name, "Visitor", existing_log.get("Date").split(" ")[1], time_str, visitor_id=visitor_id)
                            else:
                                face_match_data = {
                                    "Name": visitor_name, 
                                    "Date": f"{today_str} {time_str}", 
                                    "Status": "Regular Visitor",
                                    "ExitTime": None
                                }
                                attendance_log.insert_one(face_match_data)
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(visitor_name, "Visitor", time_str, None, visitor_id=visitor_id)
                                
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
        return redirect(url_for('image_processing.show_captured', role_type='visitor'))

@face_auth.route('/other_auth')
def other_auth():
    return render_template('other_camera.html')

@face_auth.route('/other_modal')
def other_modal():
    import app.image_processing as imp
    import datetime
    import os
    import cv2
    from app.camera_manager import get_camera

    shot_filename = None
    if imp.captured_image:
        shot_filename = os.path.basename(imp.captured_image)
    else:
        # Fallback: If the frontend redirected before the stream could save the image
        camera = get_camera()
        success, frame = camera.read()
        if success:
            now = datetime.datetime.now()
            os.makedirs('static/shots', exist_ok=True)
            filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(filename, frame)
            imp.captured_image = filename
            shot_filename = os.path.basename(filename)
            print(f"[INFO] Fallback capture succeeded: {filename}")

    return render_template('other_modal.html', shot_filename=shot_filename)

@face_auth.route('/other_result', methods=['POST'])
@limiter.limit("6 per minute")
def other_result():
    shot_filename = request.form.get('shot_filename')
    img_path = os.path.join('static', 'shots', shot_filename) if shot_filename else None
    
    global face_match_data
    from models.vector_db import other_collection
    
    match_found = False
    
    if img_path and deepface_available and os.path.exists(img_path):
        # print(f"[INFO] Processing {img_path} for External Staff Attendance using Facenet...")
        print(f"[INFO] Processing {img_path} for External Staff Attendance using ArcFace...")
        try:
            # representations = DeepFace.represent(img_path=img_path, model_name="Facenet", enforce_detection=True)
            import time
            start_time = time.time()
            representations = DeepFace.represent(img_path=img_path, model_name="ArcFace", enforce_detection=True, detector_backend="opencv")
            latency = (time.time() - start_time) * 1000
            print(f"[BENCHMARK] ArcFace Extraction Latency (External): {latency:.2f} ms")
            
            if representations and len(representations) > 0:
                embedding = representations[0]["embedding"]
                
                if other_collection is not None and other_collection.count() > 0:
                    results = other_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["metadatas", "distances", "documents"]
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        if distance < 0.55:
                            external_id = results['ids'][0][0]
                            external_name = results['documents'][0][0] if results.get('documents') and results['documents'][0] else external_id
                            metadata = results['metadatas'][0][0] or {}
                            role = metadata.get('Role', 'External Staff')
                            
                            now = datetime.datetime.now()
                            today_str = now.strftime('%Y-%m-%d')
                            time_str = now.strftime('%H:%M:%S')
                            
                            existing_log = attendance_log.find_one({
                                "Name": external_name,
                                "Date": {"$regex": f"^{today_str}"}
                            })
                            
                            if existing_log:
                                attendance_log.update_one(
                                    {"_id": existing_log["_id"]},
                                    {"$set": {"ExitTime": time_str}}
                                )
                                face_match_data = existing_log
                                face_match_data["ExitTime"] = time_str
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(external_name, role, existing_log.get("Date").split(" ")[1], time_str, visitor_id=external_id)
                            else:
                                face_match_data = {
                                    "Name": external_name, 
                                    "Date": f"{today_str} {time_str}", 
                                    "Status": f"Present ({role})",
                                    "ExitTime": None
                                }
                                attendance_log.insert_one(face_match_data)
                                
                                # SHADOW DB INJECTION
                                from models.universal_db_helper import log_to_universal_registry
                                log_to_universal_registry(external_name, role, time_str, None, visitor_id=external_id)
                                
                            match_found = True
                            print(f"[SUCCESS] External matched: {external_name} as {role}")
        except Exception as e:
            print(f"[ERROR] External Recognition failed: {e}")

    if match_found:
        return render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)
    else:
        print("[INFO] Unknown External. Falling back to OCR.")
        return redirect(url_for('image_processing.show_captured', filename=shot_filename, role_type='external'))

@face_auth.route('/other_skip', methods=['POST'])
def other_skip():
    shot_filename = request.form.get('shot_filename')
    print("[INFO] Option B Selected. Skipping DeepFace, routing to Quick Delivery Log.")
    return redirect(url_for('image_processing.show_captured', filename=shot_filename, role_type='delivery'))
