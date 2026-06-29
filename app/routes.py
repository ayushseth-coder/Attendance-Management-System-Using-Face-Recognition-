from flask import Blueprint, render_template, redirect, url_for, session, Flask,request
from .image_processing import image_processing
import cv2
from app.camera_manager import release_camera
from flask_login import login_required

routes = Blueprint('routes', __name__, template_folder='templates')
# @routes.route('/', methods=['GET', 'POST'])
# def index():  
#   print("hello this is register")
#   return render_template('register.html')


@routes.route('/')
def login():
  return render_template('landing.html')






@routes.route("/camera")

def camera():
    return render_template("camera.html")

@routes.route("/extract")

def extract():
    return render_template("extract.html")



@routes.route('/logoutadmin')

def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@routes.route('/logoutsecurity')

def logoutsecurity():
    session.clear()
    release_camera()     
    return redirect(url_for('auth.login'))





