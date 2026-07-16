import re

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\face_auth.py', 'r') as f:
    content = f.read()

# 1. Update Visitor collection query
target1 = """                    results = visitor_collection.query(
                        query_embeddings=[embedding],
                        n_results=1
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        # Same strict threshold for Regular Visitors
                        # if distance < 0.30: 
                        if distance < 0.68: 
                            visitor_name = results['ids'][0][0].capitalize()"""

replace1 = """                    results = visitor_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["documents", "distances"]
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        if distance < 0.68: 
                            visitor_id = results['ids'][0][0]
                            visitor_name = results['documents'][0][0].capitalize() if results.get('documents') and results['documents'][0] else visitor_id"""

content = content.replace(target1, replace1)

# Update log_to_universal_registry for Visitor
target2_1 = """log_to_universal_registry(visitor_name, "Visitor", existing_log.get("Date").split(" ")[1], time_str)"""
replace2_1 = """log_to_universal_registry(visitor_name, "Visitor", existing_log.get("Date").split(" ")[1], time_str, visitor_id=visitor_id)"""
content = content.replace(target2_1, replace2_1)

target2_2 = """log_to_universal_registry(visitor_name, "Visitor", time_str, None)"""
replace2_2 = """log_to_universal_registry(visitor_name, "Visitor", time_str, None, visitor_id=visitor_id)"""
content = content.replace(target2_2, replace2_2)


# 2. Update Other collection query
target3 = """                    results = other_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["metadatas", "distances", "documents"]
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        # if distance < 0.30: 
                        if distance < 0.68:
                            external_name = results['ids'][0][0]"""

replace3 = """                    results = other_collection.query(
                        query_embeddings=[embedding],
                        n_results=1,
                        include=["metadatas", "distances", "documents"]
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        distance = results['distances'][0][0]
                        if distance < 0.68:
                            external_id = results['ids'][0][0]
                            external_name = results['documents'][0][0] if results.get('documents') and results['documents'][0] else external_id"""
content = content.replace(target3, replace3)

# Update log_to_universal_registry for Other
target4_1 = """log_to_universal_registry(external_name, role, existing_log.get("Date").split(" ")[1], time_str)"""
replace4_1 = """log_to_universal_registry(external_name, role, existing_log.get("Date").split(" ")[1], time_str, visitor_id=external_id)"""
content = content.replace(target4_1, replace4_1)

target4_2 = """log_to_universal_registry(external_name, role, time_str, None)"""
replace4_2 = """log_to_universal_registry(external_name, role, time_str, None, visitor_id=external_id)"""
content = content.replace(target4_2, replace4_2)

with open('d:\\Elgoss\\elgoss-visitor-pass\\app\\face_auth.py', 'w') as f:
    f.write(content)

print("face_auth updated successfully")
