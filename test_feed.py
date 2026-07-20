import urllib.request

try:
    req = urllib.request.urlopen('http://127.0.0.1:5001/face_video_feed', timeout=5)
    print("Status:", req.getcode())
    
    # read first few bytes to see if it's sending jpeg data
    data = req.read(200)
    print("Data:", data)
except Exception as e:
    print("Error:", e)
