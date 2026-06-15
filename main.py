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
from app.extensions import bcrypt,login_manager

  
# app = Flask(__name__, template_folder='../templates') 



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_super_secret_key_here'

    # Init extensions
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

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
