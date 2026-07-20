import re

files = [
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\face_camera.html",
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\visitor_camera.html",
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\other_camera.html"
]

target_code = '''let icon = data.status === "spoof" ? "error" : "warning";'''
replacement_code = '''let icon = data.status === "spoof" ? "error" : "warning";
                
                // Add Voice Alert
                if ('speechSynthesis' in window) {
                    let msg = new SpeechSynthesisUtterance(title + " " + text);
                    msg.rate = 0.9; // Slightly slower for clarity
                    window.speechSynthesis.speak(msg);
                }'''

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if target_code in content and "SpeechSynthesisUtterance" not in content:
        content = content.replace(target_code, replacement_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added voice alert to {file_path}")
    else:
        print(f"Skipped {file_path} (Already has voice or target code not found)")
