from app import app
from db import db, User, Search

with app.app_context():
    to_delete = ["schoogl88@gmail.com", "schoogle88@gmail.com"]

    for email in to_delete:
        user = User.query.filter_by(email=email).first()
        if user:
            # Delete this user's searches first
            Search.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            print(f"Deleted user and their searches: {email}")
        else:
            print(f"User not found: {email}")

    db.session.commit()
    print("Done.")
