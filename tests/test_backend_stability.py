import os
import sys
import pytest

# Add the parent directory to sys.path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        # Simulate a logged-in session for admin routes
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = "TestAdmin"
            sess['role'] = "Admin"
        yield client

def test_route_integrity(client):
    """
    Test that critical routes load without 500 Server Errors.
    We expect 200 (OK) or 302 (Redirects).
    """
    routes = [
        '/',
        '/login',
        '/admin_h',
        '/universal_records',
        '/visitor_over',
        '/filter_role'
    ]
    
    for route in routes:
        response = client.get(route)
        assert response.status_code != 500, f"CRASH DETECTED: Route {route} failed with status {response.status_code}"

def test_addadmin_boundary_fuzzing(client):
    """
    Fuzz test the /addadmin route with bad data to ensure backend validation
    gracefully redirects (302) instead of crashing (500).
    """
    # 1. Test completely empty payload
    response = client.post('/addadmin', data={})
    assert response.status_code == 302, "Empty payload caused a crash instead of a redirect."
    
    # 2. Test mismatched passwords
    payload = {
        'fullname': 'Fuzz User',
        'addemail': 'fuzz@test.com',
        'phone': '0000000000',
        'jobtitle': 'Intern',
        'password': 'password123',
        'passwordConfirmation': 'different_password'
    }
    response = client.post('/addadmin', data=payload)
    assert response.status_code == 302, "Mismatched passwords caused a crash instead of a redirect."
    
    # 3. Test incredibly long string for injection/boundary test
    long_string = "A" * 10000
    payload['fullname'] = long_string
    payload['passwordConfirmation'] = 'password123'
    response = client.post('/addadmin', data=payload)
    # The application should safely redirect without crashing
    assert response.status_code == 302, "Massive string input caused a crash."

def test_login_stress(client):
    """
    Test that rapid bad login attempts don't cause server exceptions.
    """
    for _ in range(10):
        response = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'})
        assert response.status_code != 500, "Stress testing /login caused a 500 crash."
