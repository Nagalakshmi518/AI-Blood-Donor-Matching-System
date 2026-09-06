import os, time, traceback
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
    print('before drop_all', flush=True)
    try:
        db.drop_all()
        print('after drop_all', flush=True)
    except Exception:
        traceback.print_exc()
        print('drop_all failed', flush=True)
    try:
        db.create_all()
        print('after create_all', flush=True)
    except Exception:
        traceback.print_exc()
        print('create_all failed', flush=True)
