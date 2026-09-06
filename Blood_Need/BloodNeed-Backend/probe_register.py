import os

os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '3306'
os.environ['DB_NAME'] = 'bloodneed_stage_validation'
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = 'admin@123'

print('before create_app', flush=True)
from app import create_app
app = create_app()
print('after create_app', flush=True)

with app.test_client() as client:
    payload = {
        'full_name': 'Probe User',
        'email': 'probe.user.1@example.com',
        'phone': '9000000001',
        'password': 'Passw0rd!',
        'role': 'PATIENT'
    }
    print('before request', flush=True)
    res = client.post('/api/auth/register', json=payload)
    print('status', res.status_code, flush=True)
    print(res.get_data(as_text=True), flush=True)
