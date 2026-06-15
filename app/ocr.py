import re,json,io,ftfy
import cv2
from flask import Blueprint, request
import pytesseract
from PIL import Image
from datetime import datetime
from models.database import otp_send
phone_data = otp_send.find_one({"phone": {"$ne": None}})  # Get a document where phone is NOT None
if phone_data:
    phone_data['_id'] = str(phone_data['_id'])  # Make _id serializable
    phone = phone_data.get('phone')  # Get the phone number
else:
    phone = None

global data
data=None
now = datetime.now().isoformat()
ocr = Blueprint('ocr', __name__)
def extract_card_details(filename):
    try:
        pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract\tesseract.exe"
       
        img = cv2.imread(filename)
        img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(img, cv2.CV_64F).var()
        
        if var < 100:
            gaussian_blur = cv2.GaussianBlur(img, (7, 7), 2)
            sharpened2 = cv2.addWeighted(img, 3.5, gaussian_blur, -2.5, 0)
            cv2.imwrite("sh2.jpg", sharpened2)
            filename = "sh2.jpg"
            

        text = pytesseract.image_to_string(Image.open(filename), lang='eng')
       

        text_output = open('output.txt', 'w', encoding='utf-8')
        text_output.write(text)
        text_output.close()

        file = open('output.txt', 'r', encoding='utf-8')
        text = file.read()

        text = ftfy.fix_text(text)
        text = ftfy.fix_encoding(text)
        data={}
        if "income" in text.lower() or "tax" in text.lower() or "department" in text.lower() or "permanent" in text.lower() or "account" in text.lower() or "number" in text.lower() or "card" in text.lower() or "father" in text.lower() or "signature" in text.lower():
            data = pan_read_data(text)
            # print("extracted data  pan   ++++++ : ",data)#chnages
        elif "male" in text.lower() or "VID" in text:
            data = adhaar_read_data(text)
        with io.open('info.json', 'w', encoding='utf-8') as outfile:
            data_str = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
            outfile.write(data_str)  # Direct string writing, no conversion needed
        with open('info.json', encoding='utf-8') as data_file:
            data_loaded = json.load(data_file)
        # print("data load---------- :",data_loaded)
        return data_loaded
    except Exception as e:
        print(f"OCR Error occurred: {e}")
        # Return an empty dict so the UI form can still render as a manual fallback
        return {}

def extract_field(pattern, text, group=0):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        if group > 0 and match.lastindex and group <= match.lastindex:
            return match.group(group).strip()
        else:
            return match.group().strip()
    return ""




def adhaar_read_data(text):
    
    name_match = re.search(r"(?i)(?:Name|नाम):?\s*(.*)", text)
    father_match = re.search(r"(?i)(?:Father's Name|पिता का नाम):?\s*(.*)", text)
    dob_match = re.search(r"(?i)(?:DOB|Date\s*of\s*Birth|जन्म\s*तिथि)[^\d]{0,10}(\d{2}/\d{2}/\d{4})", text)
    gender_match = re.search(r"(?i)(?:Male|Female|Transgender|पुरुष|महिला)", text)
    aadhaar_number = re.search(r"^\d{4}\s\d{4}\s\d{4}", text) or re.search(r"\b\d{12}\b", text)



    data={
        "phone":phone,
        "Date":now,
        "card": "Aadhaar",
        "UID": aadhaar_number.group(0) if aadhaar_number else None,
        "Name": name_match.group(1) if name_match else None,
        "Father_Name": father_match.group(1) if father_match else None,
        "dob": dob_match.group(1) if dob_match else None,
        "sex": gender_match.group(0) if gender_match else None
    }
    
    return data

def pan_read_data(text):

    pan_number = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
    name_match = re.search(r"(?i)(?:Name|नाम):?\s*(.*)", text)
    father_match = re.search(r"(?i)(?:Father's Name|पिता का नाम):?\s*(.*)", text) or re.search(r"(?i)(?:Father's\s*Name|पिता\s*का\s*नाम)\s*[:\-]?\s*(.*)", text)
    dob_match = re.search(r"(?i)(?:DOB|Date\s*of\s*Birth|जन्म\s*तिथि|जन्म\s*की\s*तारीख)[^\d]{0,10}(\d{2}/\d{2}/\d{4})", text)or re.search(r"(?i)(?:DOB|Date\s*of\s*Birth|जन्म\s*तिथि|जन्म\s*की\s*तारीख)[^\d]*([\d]{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
    gender_match = re.search(r"(?i)(?:Male|Female|Transgender|पुरुष|महिला)", text)

    data= {
        "phone":phone,
        "Date":now,
        "card": "pan",
        "UID": pan_number.group(0) if pan_number else None,
        "Name": name_match.group(1) if name_match else None,
        "Father_Name": father_match.group(1) if father_match else None,
        "dob": dob_match.group(1) if dob_match else None,
        "sex": gender_match.group(0) if gender_match else None
    }
    return data




