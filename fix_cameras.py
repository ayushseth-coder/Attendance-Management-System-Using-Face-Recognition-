import os

script_to_replace = """// After 4.5 seconds (3.3s capture + buffer), redirect to result page
setTimeout(function() {
    window.location.href = "{{ url_for('face_auth.REPLACE_ROUTE') }}";
}, 4500);"""

new_script = """// After 4.5 seconds (3.3s capture + buffer), fetch result via AJAX
setTimeout(function() {
    fetch("{{ url_for('face_auth.REPLACE_ROUTE') }}")
        .then(response => response.json())
        .then(data => {
            if (data.status === "spoof" || data.status === "too_close") {
                let title = data.status === "spoof" ? "Fake Face Detected!" : "Too Close to Camera!";
                let text = data.status === "spoof" ? "Please show your real face." : "Please step back a bit.";
                let icon = data.status === "spoof" ? "error" : "warning";
                
                let timerInterval;
                Swal.fire({
                    title: title,
                    html: text + '<br><br>Restarting in <b>3</b> seconds.',
                    icon: icon,
                    timer: 3000,
                    timerProgressBar: true,
                    showConfirmButton: false,
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    didOpen: () => {
                        const b = Swal.getHtmlContainer().querySelector('b');
                        timerInterval = setInterval(() => {
                            b.textContent = Math.ceil(Swal.getTimerLeft() / 1000);
                        }, 100);
                    },
                    willClose: () => {
                        clearInterval(timerInterval);
                    }
                }).then(() => {
                    window.location.reload();
                });
            } else if (data.status === "redirect") {
                window.location.href = data.url;
            } else if (data.status === "success") {
                document.open();
                document.write(data.html);
                document.close();
            }
        });
}, 4500);"""

sweetalert_tag = '<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>\n</head>'

files = [
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\face_camera.html", "face_result"),
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\visitor_camera.html", "visitor_result"),
    (r"d:\Elgoss_project\elgoss-visitor-pass\templates\other_camera.html", "other_modal")
]

for filepath, route_name in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        old_str = script_to_replace.replace("REPLACE_ROUTE", route_name)
        new_str = new_script.replace("REPLACE_ROUTE", route_name)
        
        content = content.replace(old_str, new_str)
        
        if '<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>' not in content:
            content = content.replace('</head>', sweetalert_tag)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
