from app.models.user import UserTable

class UserRepository:

        @staticmethod
        def get_user_by_email(db,email):
            return db.query(UserTable).filter(UserTable.email == email).first()
        

# Why:

# DB queries only

# No business rules

# Makes code testable