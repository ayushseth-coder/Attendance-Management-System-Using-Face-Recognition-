import re

files = [
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\face_camera.html",
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\visitor_camera.html",
    r"d:\Elgoss_project\elgoss-visitor-pass\templates\other_camera.html"
]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the image tag
    # For face_camera: src="{{ url_for('face_auth.face_video_feed') }}"
    # For visitor_camera: src="{{ url_for('image_processing.video_feed') }}"
    # For other_camera: src="{{ url_for('image_processing.video_feed') }}"
    
    # We can replace the simple src with a script that adds a timestamp to prevent caching
    
    # Let's replace: src="{{ url_for('face_auth.face_video_feed') }}"
    content = content.replace(
        '''src="{{ url_for('face_auth.face_video_feed') }}"''',
        '''id="camera-feed" src=""'''
    )
    
    content = content.replace(
        '''src="{{ url_for('image_processing.video_feed') }}"''',
        '''id="camera-feed" src=""'''
    )
    
    # Append the script before the closing </body> tag if not already there
    script_str = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        var img = document.getElementById("camera-feed");
        if(img) {
            var url = "";
            if (window.location.href.includes("face_login")) {
                url = "{{ url_for('face_auth.face_video_feed') }}";
            } else {
                url = "{{ url_for('image_processing.video_feed') }}";
            }
            img.src = url + "?t=" + new Date().getTime();
        }
    });
</script>
</body>"""

    if 'id="camera-feed"' in content and "document.getElementById(\"camera-feed\")" not in content:
        content = content.replace("</body>", script_str)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Video stream cache-buster applied.")
