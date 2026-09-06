from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():

    existing = User.query.filter_by(email="admin@gmail.com").first()

    if existing:
        print("Admin already exists.")

    else:

        admin = User(

            full_name="Administrator",

            email="admin@gmail.com",

            phone="8888888888",

            password=generate_password_hash("admin123"),

            role="ADMIN",

            active=True

        )

        db.session.add(admin)

        db.session.commit()

        print("Admin created successfully!")