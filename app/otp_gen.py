import random
import smtplib
from flask import Flask,Blueprint,render_template,request,flash,session,redirect
from email.mime.text import MIMEText
import pyotp
from config.setting import TWILIO_AUTH_TOKEN,TWILIO_ACCOUNT_SID, TWILIO_PHONE_NUMBER,SMTP_PORT,SMTP_SERVER,SENDER_EMAIL,SENDER_PASSWORD
from werkzeug.security import generate_password_hash
from models.database import otp_send,collection
from twilio.rest import Client
from flask_login import login_required
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
otp_gen= Blueprint('otp_gen', __name__)


def otp_genrator():
        secret = pyotp.random_base32()
        # Create a TOTP object (Time-based One-Time Password)
        totp = pyotp.TOTP(secret)
        
        # Generate a 6-digit OTP
        otp = totp.now()
       
        otp_4_digit = otp[:4]
       
        
        return otp_4_digit

  
@otp_gen.route("/forgot", methods=['POST','GET'])

def forgot():

    return render_template('forgot.html')  

  
@otp_gen.route("/verify", methods=['POST','GET'])

def reset():
    
    print("this is the verify")
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash("Email cannot be empty.", "danger")
            return render_template('forgot.html')
            
        Exist_email = collection.find_one({"Email": email})
       
       

        if Exist_email:
            sender_email = SENDER_EMAIL
            sender_password = SENDER_PASSWORD
           
            smtp_server = SMTP_SERVER
            smtp_port =SMTP_PORT
            recipient_email = Exist_email["Email"]
            
          
            otp = otp_genrator()
            print(f"genrate otp-------{otp}")
            data={
                'otp_here':otp
            }
            otp_send.insert_one(data)
           
            subject = "Your OTP"
            body = f"Your OTP is: {otp}"

            # Send the email
            try:
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = recipient_email

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()  # Enable TLS encryption
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    session['reset_email'] = Exist_email['Email']  #start the session of exist email in your db
                print(f"OTP '{otp}' sent to {recipient_email}")
            except Exception as e:
                print(f"Error sending email: {e}")
            return render_template('verify.html') 
        else:
            flash("Invalide Email Please Check It", "danger")
            return render_template('forgot.html')

    
@otp_gen.route("/otp_match", methods=['POST','GET']) 
    
def match():
    if request.method == 'POST':
        c_otp = request.form.get('o', '') + request.form.get('to', '') + request.form.get('th', '') + request.form.get('f', '')
        
        if len(c_otp) != 4 or not c_otp.isdigit():
            flash("Invalid OTP format. Must be 4 digits.", "danger")
            return render_template('verify.html')
            
        print(f"verification{c_otp}")
        Exist_otp=otp_send.find_one({"otp_here":c_otp})
        if Exist_otp:
            print(f"exist otp===={Exist_otp}")
            return render_template('reset_pass.html')
        else:
            flash("OTP Invalid Please Check It", "danger")
            return render_template('verify.html') 
       
        

  

@otp_gen.route('/reset-password', methods=['GET', 'POST'])

def reset_password():
    email = session.get('reset_email')
    if not email:
        flash("Session expired. Please try again.", "error")
        return redirect('/forgot')

    if request.method == 'POST':
        new_pass = request.form.get('new_pass', '')
        confirm_pass = request.form.get('confirm_pass', '')

        if len(new_pass) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect('/reset-password')

        if new_pass != confirm_pass:
            flash("Passwords do not match.", "error")
            return redirect('/reset-password')
       
        hashed = generate_password_hash(new_pass)
        # CRITICAL SECURITY FIX: Save the hashed password, not the plaintext confirm_pass
        collection.update_one({"Email": email}, {"$set": {"Password": hashed}})
        session.pop('otp', None)
        session.pop('reset_email', None)

        flash("Password updated successfully.", "success")
        return render_template('login.html')

    return render_template('reset_pass.html')



@otp_gen.route('/send_sms', methods=['GET', 'POST'])

def send_sms():
    global message
    message=None
    if request.method == 'POST':
        phone = request.form['phone']
        otp = otp_genrator()
        print(f"sms otp from twilio phone number   sending {TWILIO_PHONE_NUMBER}")
        data={
                'sms_otp':otp,
                'phone':phone
            }
        otp_send.insert_one(data)
        session['otp'] = otp
        session['phone'] = phone
       
        # DEVELOPMENT MODE BYPASS
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        # from_=TWILIO_PHONE_NUMBER,
        # body=f"Your OTP is {otp}",
        # to=phone
        # )
        
        print(f"DEV MODE: Bypassing SMS for phone {phone}. OTP was {otp}")
        return render_template('camera.html')
        
        # return render_template('sms_verify.html')
    return render_template('sms.html') 

    
@otp_gen.route("/sms_match", methods=['POST','GET'])   
   
def sms_match():
    if request.method == 'POST':
      
       
        c_otp=request.form['o'] 
        c_otp +=request.form['to']
        c_otp +=request.form['th']
        c_otp +=request.form['f']
        print(f"verification{c_otp}")
        Exist_otp=otp_send.find_one({"sms_otp":c_otp})
        if Exist_otp:
            print(f"exist otp===={Exist_otp}")
            return render_template('camera.html')
        else:
            flash("OTP Invalid Please Check It", "danger")
            return render_template('sms_verify.html') 


        
    
             
             
             
     