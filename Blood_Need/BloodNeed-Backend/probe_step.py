import os, time
os.environ['DB_HOST']='localhost'
os.environ['DB_PORT']='3306'
os.environ['DB_NAME']='bloodneed_stage'
os.environ['DB_USER']='root'
os.environ['DB_PASSWORD']='admin@123'
print('START', flush=True)
from app import create_app, db
app = create_app()
print('APP_READY', flush=True)
with app.app_context():
    print('DROP_START', flush=True)
    db.drop_all()
    print('DROP_DONE', flush=True)
    db.create_all()
    print('CREATE_DONE', flush=True)
with app.test_client() as c:
    payload={'full_name':'Test User','email':'probe.user@example.com','phone':'9000000001','password':'Passw0rd!','role':'PATIENT'}
    print('REQUEST_START', flush=True)
    r = c.post('/api/auth/register', json=payload)
    print('status', r.status_code, flush=True)
    print(r.get_data(as_text=True)[:500], flush=True)
    print('elapsed', round(time.time(),2), flush=True)
