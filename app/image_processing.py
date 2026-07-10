from flask import Blueprint, render_template, request, Response
import cv2
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
    global captured_image, captured_data
    camera = get_camera()
    captured_data = None
    captured_image = None
    start_time = time.time()
    countdown_duration = 5.0  # reduced to 5 seconds
    
    try:
        while True:
            success, frame = camera.read()
            if not success:
                time.sleep(0.1)
                continue

            elapsed_time = time.time() - start_time

            # # After countdown, detect card and capture
            if elapsed_time >= countdown_duration and captured_image is None:
                now = datetime.datetime.now()
                os.makedirs('static/shots', exist_ok=True)  # save to static to render in HTML
                filename = os.path.join('static', 'shots', f"shot_{now.strftime('%Y%m%d_%H%M%S')}.png")
                cv2.imwrite(filename, frame)
                captured_image = filename
                print(f"[INFO] Image captured and saved to {filename}")
                break

            # Encode the current frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
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