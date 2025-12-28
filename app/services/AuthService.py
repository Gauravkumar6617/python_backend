from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserOut, LoginResponse
from app.core.security import verify_password, create_token

class AuthService:

    @staticmethod
    def login(data, db):
        user_instance = UserRepository.get_user_by_email(db, data.email)

        if not user_instance or not verify_password(data.password, user_instance.password):
            raise Exception(401, "Invalid Credentials")
         
        token = create_token(user_instance.id)
        user_data = UserOut.from_orm(user_instance)  # must be instance

        return LoginResponse(access_token=token, user=user_data)
