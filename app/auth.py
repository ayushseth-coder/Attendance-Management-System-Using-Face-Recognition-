
from flask import Blueprint, request, render_template, jsonify, redirect, url_for,session,flash
from werkzeug.utils import secure_filename
from werkzeug.security import  check_password_hash
import os
from flask_bcrypt import Bcrypt
# from bson import ObjectId  
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from models.database import collection
from app.extensions import bcrypt,login_manager

from models.user import User
users = User
 
auth = Blueprint('auth', __name__)
  

class User(UserMixin):
    def __init__(self, user_id, username, email, password,Job):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.Job= Job


@login_manager.user_loader
def load_user(user_id):
    return users.get_by_id(user_id)





@ auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = collection.find_one({"Email": email})
        print(f"user data  {user_data}")
        
        if not user_data:
            flash("Invalid email and Password", "danger")
            return redirect(url_for('auth.login'))

        # Check password
        if bcrypt.check_password_hash(user_data["Password"], password):
            role = user_data.get("Job", "").lower()
            login_type = request.form.get('login_type')
            
            if login_type and login_type != role:
                flash("You are not authorized to login from this portal.", "danger")
                return redirect(url_for('auth.login'))

            user = User(
                str(user_data["_id"]),
                user_data["Name"],
                user_data["Email"],
                user_data["Password"],
                user_data["Job"]
            )

            login_user(user)
            print(f"user data role:{role}")
            if role == "admin":
                session['user_id'] = email
                  
                session['logged_in'] = True
                
                return redirect(url_for('admin.admin_h')) 
            elif role == "security":
                session['user_id'] = email    
                session['logged_in'] = True
                return redirect(url_for('security.security_home'))  
            else:
                flash("Invalid role", "danger")
                return redirect(url_for('auth.login'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('auth.login'))

    return render_template("login.html")

@ auth.route('/profile', methods=['POST', 'GET'])
def profile():
    if session.get('user_id'):
        email = session.get('user_id')
        user_data = collection.find_one({"Email": email})
        if user_data :
            # Convert _id to string
            user_data['_id'] = str(user_data['_id'])
            name = user_data.get('Name', '')  
            role=user_data.get('Job', '').lower()
            if role == "security":
                
                return render_template('profile_security.html', user_data=user_data, name=name, email=email)
            elif role == "admin":
               
                return render_template('profile_admin.html', user_data=user_data, name=name, email=email)  
            else :
                
                return redirect(url_for('auth.login'))
        
        else:
            return render_template('error.html', message="User data not found.")
  

        
@ auth.route('/view_profile', methods=['POST', 'GET'])
def view_profile():
    if 'user_id' in session:
        email = session['user_id']
        user_data = collection.find_one({'Email': email})
        if user_data:
            user_data['_id'] = str(user_data['_id'])  
            return render_template('view_profile.html', user_data=user_data)
        else:
            return render_template('error.html', message="User not found.")
    else:
        
      return render_template('auth.view_profile')




@auth.route('/update_profile', methods=['POST','GET'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    email = session['user_id']
    updated_data = {
        'Name': request.form.get('Name'),
        'mobile': request.form.get('mobile'),
        'address': request.form.get('address'),
        'Job': request.form.get('Job')
    }

    result = collection.update_one({'Email': email}, {'$set': updated_data})

    flash("Profile updated successfully!" if result.modified_count else "No changes made.")
    return redirect(url_for('auth.profile'))


@ auth.route('/cancle', methods=['POST', 'GET'])
def cancle():
                 
    return redirect(url_for('auth.profile'))

@auth.route('/upload_profile_image', methods=['POST'])
def upload_profile_image():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    file = request.files.get('profile_image')
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join('static/images', filename)
        file.save(save_path)

        # Update DB
        email = session['user_id']
        collection.update_one({'Email': email}, {'$set': {'profile_image': f'static/images/{filename}'}})

    return redirect(url_for('profile')) 
