import datetime
import logging

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from socialapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "6754e1fcb5f9b69e88d7b14e3f036460e89b54fdab026b547d132ee819d4fc22"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials"
)  # custom error exception


def access_token_expire_minutes() -> int:  # used for testing so mocking is easier
    return 30


def create_access_token(email: str):  # storing email since email is unique
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """hasing password twice doesn't get same password, seed is stored inside hashed password
    which is why we need to use verify instead of hashing again and using =="""
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    logger.debug("Fetching user from the database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user
