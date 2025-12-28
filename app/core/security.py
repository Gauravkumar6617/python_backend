# from passlib.context import CryptContext
# from jose import jwt
# from datetime import datetime, timedelta, timezone
# from app.core.config import settings

# # Use Argon2 first, then fallback to bcrypt
# pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# # Hash a password
# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)

# # Verify a password
# def verify_password(raw_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(raw_password, hashed_password)

# # JWT token creation
# def create_token(user_id: int) -> str:
#     expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
#     payload = {
#         "sub": str(user_id),   # Standard: 'sub' as string
#         "exp": expire,
#         "iat": datetime.now(timezone.utc)
#     }
    
#     encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#     return encoded_jwt


from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

# ✅ Use ONLY argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(raw_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(raw_password, hashed_password)

def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
