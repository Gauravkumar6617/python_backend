from passlib.context import CryptContext

# ✅ Use ONLY argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def generate_password_hash(password: str) -> str:
    return pwd_context.hash(password)

if __name__ == "__main__":
    raw_password = input("Enter password: ")
    hashed = generate_password_hash(raw_password)
    print("\nHashed password:\n")
    print(hashed)
