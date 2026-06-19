from app.ocr import ocr



from flask import Flask,render_template
from config.setting import MONGO_URI,SECRET_KEY
from app.routes import routes
from app.auth import auth
from app.visitors import visitor
from app.admin import admin
from app.security import security
from app.otp_gen import otp_gen
from app.image_processing import image_processing
from app.extensions import bcrypt, login_manager, limiter
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler

def cleanup_old_shots():
    shots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'shots')
    if not os.path.exists(shots_dir):
        return
    
    current_time = time.time()
    for filename in os.listdir(shots_dir):
        file_path = os.path.join(shots_dir, filename)
        if os.path.isfile(file_path) and filename.endswith('.png'):
            # Check if file is older than 24 hours (86400 seconds)
            if os.path.getmtime(file_path) < current_time - 86400:
                try:
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted old shot: {filename}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete {filename}: {e}")


  
# app = Flask(__name__, template_folder='../templates') 



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_super_secret_key_here'

    # Init extensions
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    limiter.init_app(app)

    # Init APScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_old_shots, trigger="interval", hours=24)
    scheduler.start()


    # Register blueprints
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(routes)
    app.register_blueprint(otp_gen)
    app.register_blueprint(image_processing)
    app.register_blueprint(visitor)
    app.register_blueprint(admin)
    app.register_blueprint(security)
    app.register_blueprint(ocr)
    
    from app.face_auth import face_auth
    app.register_blueprint(face_auth)

    return app
