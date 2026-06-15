from pymongo import MongoClient
from bson import SON
from config.setting import MONGO_URI

client = MongoClient(MONGO_URI)
db = client['visitor_management']

collection = db['users']
adminlog = db['admin_log']
securitylog = db['security_log']
visitorlogtable = db['visitor_log']
activevisitorstable = db['active_visitors']
reqvistable = db['request']
rejectedvistable = db['rejected_visitors']
otp_send=db['otp_store']
visitors_status=db['status']
attendance_log = db['attendance_log']
