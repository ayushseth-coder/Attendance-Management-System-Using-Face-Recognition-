import requests

url = "http://127.0.0.1:5001/auth/login"
data = {
    "login_type": "security",
    "email": "security@security.com",
    "password": "security123"
}

try:
    response = requests.post(url, data=data, allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    if response.status_code == 302:
        print(f"Redirects to: {response.headers['Location']}")
    else:
        print(f"Response Body: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
