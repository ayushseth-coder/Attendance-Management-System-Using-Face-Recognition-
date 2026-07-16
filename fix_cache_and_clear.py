import os

filepath = r"d:\Elgoss_project\elgoss-visitor-pass\app\face_auth.py"
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

# Add imp.captured_images.clear() before returning too_close and spoof
code = code.replace('return jsonify({"status": "too_close"})', 
                    'imp.captured_images.clear()\n                    return jsonify({"status": "too_close"})')

code = code.replace('return jsonify({"status": "spoof"})', 
                    'imp.captured_images.clear()\n                    return jsonify({"status": "spoof"})')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)


# Fix frontend caching in fetch
files = [
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\face_camera.html", "face_result"),
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\visitor_camera.html", "visitor_result"),
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\other_camera.html", "other_modal")
]

for fp, route in files:
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        
        target_fetch = f'fetch("{{{{ url_for(\'face_auth.{route}\') }}}}")'
        new_fetch = f'fetch("{{{{ url_for(\'face_auth.{route}\') }}}}?t=" + new Date().getTime())'
        
        if target_fetch in content:
            content = content.replace(target_fetch, new_fetch)
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)

print("Fixes applied.")
