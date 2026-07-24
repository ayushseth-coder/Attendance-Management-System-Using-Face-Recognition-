// Centralized function to handle Anti-Spoofing and Liveness alerts for camera feeds
function handleFaceAlerts(data) {
    if (data.status === "spoof" || data.status === "too_close") {
        let title = data.status === "spoof" ? "Fake Face Detected!" : "Too Close to Camera!";
        let text = data.status === "spoof" ? "Please show your real face." : "Please step back a bit.";
        let icon = data.status === "spoof" ? "error" : "warning";

        // Add Voice Alert
        if ('speechSynthesis' in window) {
            console.log("Triggering Voice Alert: " + title);
            let msg = new SpeechSynthesisUtterance(title + " " + text);
            msg.rate = 1.3; // Speak 30% faster to finish before reload
            msg.volume = 1.0; // 1.0 is the maximum volume allowed by browsers
            msg.lang = 'en-US'; // Force English voice
            window.speechSynthesis.cancel(); // Clear any stuck speech
            window.speechSynthesis.speak(msg);
        }

        if (typeof Swal !== 'undefined') {
            let timerInterval;
            Swal.fire({
                title: title,
                html: text + '<br><br>Restarting in <b>4</b> seconds.',
                icon: icon,
                timer: 4000,
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
        } else {
            alert(title + "\n" + text);
            window.location.reload();
        }
        return true; // Handled
    }
    return false; // Not a face alert
}
