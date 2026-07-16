with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'r') as f:
    content = f.read()

target = '''                # Extract Name from filename (e.g. "Anshuman.jpg" -> "Anshuman")
                employee_name = os.path.splitext(filename)[0].capitalize()
                
                try:
                    # Run AI Extraction
                    # representations = DeepFace.represent(img_path=filepath, model_name="Facenet", enforce_detection=False)
                    representations = DeepFace.represent(img_path=filepath, model_name="ArcFace", enforce_detection=False)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        
                        # Save to Vector DB
                        employee_collection.upsert(
                            ids=[employee_name],
                            embeddings=[embedding],
                            metadatas=[{"path": filepath}]
                        )'''

replacement = '''                # Extract Name and ID from filename (e.g. "Anshuman0055.jpg" -> "Anshuman", "0055")
                import re
                base_name = os.path.splitext(filename)[0]
                match = re.match(r"([A-Za-z]+)(\\d*)", base_name)
                if match:
                    employee_name = match.group(1).capitalize()
                    extracted_id = match.group(2) if match.group(2) else None
                else:
                    employee_name = base_name.capitalize()
                    extracted_id = None
                
                formal_emp_id = f"EMP-{extracted_id}" if extracted_id else f"EMP-{employee_name.upper()}"
                
                try:
                    # Run AI Extraction
                    # representations = DeepFace.represent(img_path=filepath, model_name="Facenet", enforce_detection=False)
                    representations = DeepFace.represent(img_path=filepath, model_name="ArcFace", enforce_detection=False)
                    
                    if representations and len(representations) > 0:
                        embedding = representations[0]["embedding"]
                        
                        # Save to Vector DB
                        employee_collection.upsert(
                            ids=[employee_name],
                            embeddings=[embedding],
                            metadatas=[{"path": filepath, "EmpID": formal_emp_id}]
                        )
                        
                        # SHADOW DATA: Pre-Register in Universal Database
                        from models.database import universal_registry
                        import datetime
                        universal_registry.update_one(
                            {"_id": formal_emp_id},
                            {"$setOnInsert": {
                                "Name": employee_name,
                                "Role": "Employee",
                                "Phone": "Unknown",
                                "Email": "Unknown",
                                "Address": "Unknown",
                                "Leave_Status": "Active",
                                "Visitor_Type": "Regular",
                                "Attendance_Logs": []
                            }},
                            upsert=True
                        )'''

if target in content:
    content = content.replace(target, replacement)
    with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\admin.py', 'w') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found!")
