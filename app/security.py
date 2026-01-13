from passlib.context import CryptContext

# 1. Setup the hashing engine
# We use 'bcrypt', which is the industry standard for security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    #encryption
    return pwd_context.hash(password)

