 
 Project Structure
 
 /visitor_management_system
├── /app
│   ├── __init__.py
│   ├── routes.py
│   ├── auth.py
│   ├── visitor.py
│   ├── admin.py
│   ├── security.py
│   ├── image_processing.py
│   ├── ocr.py
│   └── utils.py
├── /models
│   ├── __init__.py
│   ├── visitor.py
│   ├── user.py
│   ├── logs.py
│   └── database.py
├── /templates
│   ├── security_dashboard.html
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── visitor_dashboard.html
├── /static
│   ├── /css
│   ├── /js
│   └── /images
├── /config
│   ├── __init__.py
│   ├── settings.py
│   └── database.py
├── /tests
├── requirements.txt
├── .env
├── app.py
├── run.py



 Data Storage & Management

Visitor data is stored in MongoDB.

Image files are saved in the shots/ directory.

Logs and security records are managed for auditing.





Tools Used

1. Flask (Backend Framework)

Handles HTTP requests, user authentication, and routing.

2. MongoDB (Database)

Stores visitor records, user credentials, and logs.

3. OpenCV (Image Processing)

Captures and preprocesses identity card images.

4. Tesseract OCR (Optical Character Recognition)

Extracts text from Aadhaar and PAN cards.

5. Bootstrap (Frontend UI)

Provides a responsive and user-friendly interface.

6. Flask-Flash (User Notifications)

Displays success or error messages during authentication.

Deployment

Install dependencies:

pip install -r requirements.txt

Run the Flask application:

flask run 

### Database Schema
The project uses MongoDB with the following collections:
1. users (Stores admin and security users)
2. VisitorLog (Records all visitors)
3. ActiveVisitors (Tracks currently active visitors)
4. RequestedVisitor (Stores visitor requests pending approval)
5. AcceptedVisitors (Tracks approved visitors)
6. RejectedVisitors (Stores rejected visitor entries)
7. SecurityUsers (Security personnel data)
8. AdminUsers (Admin data)




Workflow

step 1.  The (/) page allows users to authenticate using their email and password.

step 2. After the submit email and password then redirect the auth route and call the authenticate function and 
        compaire the email and password if email and password match the admin then redirect the admin_dashboard ,
        if match the security then redirect the security_dashboard.

step 3. if After login page redirect the security_dashboard the start the camera and show the security_dashboard
        page.

step 4. if capture the Image click on capture then store the image in shots folder and also create the dynamic 
        name of image sh2.jpg in visit folder.

step 4. sh2.jpg is the comprase image and it's image use the Extracts image to string 

step 5. after convert the string then seprate the all text like Name, Caard Number ,UID etc
        after seprated send the data in html page in set information  through the value and then click the visit pass 
        then save the db 

step 6. After click the visit pass then redirect the same page (security_dashboard)

step 7. After the store data in db then show the data in  visiter overview 

step 7. if login the admin_dashboard then you  Approved the visiter is visit or not if you open the Notifications then see the how many pepole 
        is visit and you accept and reject the visitors

step 8.  After Accepted or Rejected the visiters you see the visiters overview     

step 9. you see the same page users overview and the click on then  see the how many id is register , id means security and Admin


hello this is test changes....