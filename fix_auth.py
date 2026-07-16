import os

filepath = r"d:\Elgoss_project\elgoss-visitor-pass\app\face_auth.py"
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add jsonify
code = code.replace("from flask import Blueprint, render_template, request, Response, redirect, url_for", 
                    "from flask import Blueprint, render_template, request, Response, redirect, url_for, jsonify")

# 2. Frame check fix
old_frame_check = """                if not is_real:
                    print(f"[WARNING] Spoofing Detected on frame! (Score: {score:.2f})")
                    results_list.append("Spoof")
                    continue"""
new_frame_check = """                if is_real == "TooClose":
                    results_list.append("TooClose")
                    continue
                elif not is_real:
                    results_list.append("Spoof")
                    continue"""
code = code.replace(old_frame_check, new_frame_check)

# 3. Winner check fix
old_winner_check = """                if winner != "Unknown" and votes >= (len(imp.captured_images) // 2 + 1):"""
new_winner_check = """                if winner == "TooClose":
                    return jsonify({"status": "too_close"})
                elif winner == "Spoof":
                    return jsonify({"status": "spoof"})
                elif winner != "Unknown" and votes >= (len(imp.captured_images) // 2 + 1):"""
code = code.replace(old_winner_check, new_winner_check)

# 4. Success returns
code = code.replace("return render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)",
                    "return jsonify({\"status\": \"success\", \"html\": render_template('attendance_success.html', data=face_match_data, shot_filename=shot_filename)})")

# 5. Redirect returns
code = code.replace("return redirect(url_for('image_processing.show_captured', role_type='employee'))",
                    "return jsonify({\"status\": \"redirect\", \"url\": url_for('image_processing.show_captured', role_type='employee')})")

code = code.replace("return redirect(url_for('image_processing.show_captured', role_type='visitor'))",
                    "return jsonify({\"status\": \"redirect\", \"url\": url_for('image_processing.show_captured', role_type='visitor')})")

code = code.replace("return redirect(url_for('image_processing.show_captured', filename=shot_filename, role_type='external'))",
                    "return jsonify({\"status\": \"redirect\", \"url\": url_for('image_processing.show_captured', filename=shot_filename, role_type='external')})")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated face_auth.py successfully.")
