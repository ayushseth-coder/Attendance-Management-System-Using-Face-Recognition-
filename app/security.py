from flask import Blueprint, request, redirect, url_for,render_template,flash, session
from models.database import collection, securitylog,visitorlogtable,activevisitorstable,rejectedvistable,visitors_status
from werkzeug.security import generate_password_hash
from flask_login import login_required
from datetime import datetime
from pymongo import ASCENDING 
security = Blueprint('security', __name__, template_folder='templates')
visitobj = list(visitorlogtable.find())
activeobj = list(activevisitorstable.find())

rejectobj = list(rejectedvistable.find())

secobj = list(securitylog.find())


reject=len(rejectobj)
countvis = len(visitobj)
active = len(activeobj)
total=countvis+reject

approvedby = ""

@security.before_request
def require_security_login():
    if request.endpoint and 'static' in request.endpoint:
        return
    if not session.get('logged_in') or session.get('role') != 'security':
        flash("You do not have permission to access the security portal.", "danger")
        return redirect(url_for('auth.login'))

@security.route('/addsec', methods=['POST','GET'])

def add_security():
   if request.method == 'POST':
        if request.form['submit'] == 'pass':
            name1 = request.form['fullname']
            email1 = request.form['addemail']
            phone = request.form['phone']
            job = request.form['jobtitle']
            password = request.form['password']
            hashed_password = generate_password_hash(password)
            daobject = {
                "Name": name1,
                "Email": email1,
                "Phone": phone,
                "Job": job,
                "Password": hashed_password, 
            }

          

        collection.insert_one(daobject)
        securitylog.insert_one(daobject)
        return redirect(url_for('auth.login'))  # Redirect to the login page


@security.route('/securitydash',methods=['GET','POST'])
def securitydash():
    pan_data={}
 

    from_date = request.form.get('FromDate')
    to_date = request.form.get('ToDate')

    query = {}

    if from_date and to_date:
        try:
            from_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_obj = datetime.strptime(to_date, '%Y-%m-%d')
            query['Date'] = {"$gte": from_date, "$lte": to_date}

        except ValueError:
            pass  

    visitors = visitors_status.find(query).sort("Date", ASCENDING)
    
    visitobj = list(visitorlogtable.find())
    activeobj = list(activevisitorstable.find())
    return render_template('visitor.html', data=pan_data, visitobj=visitobj, activeobj=activeobj, approvedby=approvedby,visit=visitors)


@security.route("/visitor", methods=["GET"])
def visitor():   
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Default to today if no dates are provided
    if not start_date_str or not end_date_str:
        start_date_str = datetime.today().strftime("%Y-%m-%d")
        end_date_str = start_date_str

    print(f"startdate+++{start_date_str},end date---------{end_date_str}")
    
    # Fetch all records first because Date is stored as string in MongoDB, 
    # which makes MongoDB string range queries fail.
    all_visitors = list(visitors_status.find())
    visitobj = []

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        for v in all_visitors:
            record_date_str = v.get('Date')
            if record_date_str:
                # Clean up the string to remove any extra time parts if present
                clean_date_str = str(record_date_str).split()[0]
                record_date = None
                # Try parsing DD/MM/YYYY
                try:
                    record_date = datetime.strptime(clean_date_str, "%d/%m/%Y").date()
                except ValueError:
                    # Try parsing YYYY-MM-DD
                    try:
                        record_date = datetime.strptime(clean_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                
                if record_date and start_date <= record_date <= end_date:
                    visitobj.append(v)
        
        print(f"Filtered records: {len(visitobj)}")
    except Exception as e:
        print(f"Error in date filtering: {e}")
        visitobj = []

    return render_template("visitor.html",visitobj=visitobj, start_date=start_date_str, end_date=end_date_str)
    


@security.route("/security_home", methods=["GET"])
def security_home():
   
    return render_template("security_home.html",total=total,countvis=countvis)

@security.route('/home', methods=['POST', 'GET'])
def home():
    return render_template("security_home.html",total=total,countvis=countvis)
@security.route("/overview", methods=["GET"])
def overview():
    visitobj = list(visitorlogtable.find({"exit_time": None}))
  
    return render_template("overview.html",visitobj=visitobj)

@security.route('/security/attendance/timesheet', methods=['GET'])
def attendance_timesheet():
    from models.database import attendance_log, collection
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": "Present"
    }
    raw_logs = list(attendance_log.find(query).sort("Date", -1))
    
    all_users = list(collection.find())
    user_lookup = {}
    for user in all_users:
        name = user.get("Name", "")
        if name:
            user_lookup[name] = {
                "Email": user.get("Email", "N/A"),
                "Job": user.get("Job", "Employee")
            }
            
    timesheet_data = []
    for log in raw_logs:
        name = log.get("Name", "")
        entry_datetime_str = log.get("Date", "")
        exit_time_str = log.get("ExitTime")
        
        entry_time_str = entry_datetime_str.split(' ')[1] if ' ' in entry_datetime_str else entry_datetime_str
        
        working_hours = None
        if exit_time_str and ' ' in entry_datetime_str:
            try:
                fmt = '%H:%M:%S'
                t1 = datetime.datetime.strptime(entry_time_str, fmt)
                t2 = datetime.datetime.strptime(exit_time_str, fmt)
                
                if t2 < t1:
                    t2 += datetime.timedelta(days=1)
                    
                diff = t2 - t1
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                working_hours = f"{hours}h {minutes}m"
            except Exception as e:
                print(f"[ERROR] Failed to calculate working hours for {name}: {e}")
                working_hours = "Error"
                
        user_info = user_lookup.get(name, {"Email": "Unknown", "Job": "Unknown"})
        
        timesheet_data.append({
            "Name": name,
            "Email": user_info["Email"],
            "Job": user_info["Job"],
            "EntryTime": entry_time_str,
            "ExitTime": exit_time_str,
            "WorkingHours": working_hours
        })
        
    return render_template('attendance_timesheet.html', timesheet=timesheet_data, selected_date=selected_date)

@security.route('/security/attendance/visitor', methods=['GET'])
def attendance_visitor():
    from models.database import attendance_log
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": "Regular Visitor"
    }
    logs = list(attendance_log.find(query).sort("Date", -1))
    
    return render_template('attendance_visitor.html', logs=logs, selected_date=selected_date)

@security.route('/security/attendance/other', methods=['GET'])
def attendance_other():
    from models.database import attendance_log
    import datetime
    
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    query = {
        "Date": {"$regex": f"^{selected_date}"},
        "Status": {"$regex": r"^Present \("}
    }
    logs = list(attendance_log.find(query).sort("Date", -1))
    
    return render_template('attendance_other.html', logs=logs, selected_date=selected_date)