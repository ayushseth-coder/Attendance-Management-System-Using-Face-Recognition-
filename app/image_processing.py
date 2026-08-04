from flask import Blueprint, render_template, request, Response
import cv2
import base64
import datetime
import os
import time
from app.camera_manager import get_camera,release_camera
from app.ocr import extract_card_details

def record(out):
    global rec, camera
    while rec:
        success, frame = camera.read()
        if success:
            out.write(frame)
        time.sleep(0.05)
   
image_processing = Blueprint('image_processing', __name__)

global pan_data, frame, captured_data, captured_image, captured_images
pan_data=None
frame=None
capture = 0
captured_data = None
captured_image = None
captured_images = []

def gen_frames():
    global captured_image, captured_data, captured_images
    camera = get_camera()
    captured_data = None
    captured_image = None
    captured_images = []
    start_time = time.time()
    countdown_duration = 3.0  # reduced to 3 seconds
    burst_captured = False
    
    try:
        while True:
            success, frame = camera.read()
            if not success:
                time.sleep(0.1)
                continue

            elapsed_time = time.time() - start_time

            # Fast rapid 3-shot burst capture after initial countdown
            if elapsed_time >= countdown_duration and not burst_captured:
                burst_captured = True
                now = datetime.datetime.now()
                os.makedirs('static/shots', exist_ok=True)
                
                for i in range(3):
                    succ, burst_frame = camera.read()
                    if succ:
                        filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}_{i}.png")
                        cv2.imwrite(filename, burst_frame)
                        captured_images.append(filename)
                        if i == 0:
                            captured_image = filename # Legacy support
                    time.sleep(0.1)
                
                print(f"[INFO] Burst captured for Visitor/General: {captured_images}")
                break # Freeze frame on frontend and release camera
            
            # Encode the current frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        release_camera()


@image_processing.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@image_processing.route('/show_captured')
def show_captured():
    from flask import request
    global captured_data, captured_image, captured_images
    
    # Check for strict role routing
    role_type = request.args.get('role_type', 'visitor')
    
    # --- MULTI-SHOT CAPTURE LOGIC ---
    if captured_images:
        shot_filename = ",".join([os.path.basename(path) for path in captured_images])
    else:
        shot_filename = os.path.basename(captured_image) if captured_image else None
        
    print(f"[DEBUG-SHOW] captured_images list length: {len(captured_images)}")
    print(f"[DEBUG-SHOW] shot_filename: {shot_filename}")

    # Skip OCR completely if it is an Employee Registration!
    if role_type == 'employee':
        return render_template('kiosk_employee_form.html', shot_filename=shot_filename, role_type=role_type)
        
    if captured_image:
        print("[INFO] Processing captured image for OCR...")
        # OCR is temporarily disabled by user request
        # captured_data = extract_card_details(captured_image)
        captured_data = {}
    
    if captured_data is None:
        captured_data = {}

    approvedby = ""  
    
    return render_template('extract.html', data=captured_data, approvedby=approvedby, shot_filename=shot_filename, role_type=role_type)


@image_processing.route('/save_webcam_frame', methods=['POST'])
def save_webcam_frame():
    global captured_image, captured_images, captured_data
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return {'status': 'error', 'message': 'No image data'}, 400
        
        img_data = data['image']
        if ',' in img_data:
            img_data = img_data.split(',')[1]
            
        image_bytes = base64.b64decode(img_data)
        now = datetime.datetime.now()
        os.makedirs('static/shots', exist_ok=True)
        filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}_0.png")
        
        with open(filename, 'wb') as f:
            f.write(image_bytes)
            
        captured_image = filename
        captured_images = [filename]
        captured_data = {}
        print(f"[SUCCESS] Browser webcam image saved: {filename}")
        return {'status': 'success', 'filename': filename}, 200
    except Exception as e:
        print(f"[ERROR] Failed to save browser webcam frame: {e}")
        return {'status': 'error', 'message': str(e)}, 500