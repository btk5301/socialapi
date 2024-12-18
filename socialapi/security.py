import datetime
import logging
from typing import Annotated, Literal

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from socialapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "6754e1fcb5f9b69e88d7b14e3f036460e89b54fdab026b547d132ee819d4fc22"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)  # populates the automated documentation for fastapi and also grabs the token from request if called as a function
pwd_context = CryptContext(schemes=["bcrypt"])

""" credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)  # custom error exception, convert to function """


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expire_minutes() -> int:  # used for testing so mocking is easier
    return 30


def confirm_token_expire_minutes() -> int:  # used for testing so mocking is easier
    return 1440


def create_access_token(email: str):  # storing email since email is unique
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {
        "sub": email,
        "exp": expire,
        "type": "access",
    }  # add type to tell which type of token the user has sent us
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):  # storing email since email is unique
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {
        "sub": email,
        "exp": expire,
        "type": "confirmation",
    }  # add type to tell which type of token the user has sent us
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token_type(
    token: str,
    type: Literal[
        "access", "confirmation"
    ],  # change from str to literal to select exact values
) -> str:
    try:  # only have code inside try that will possibly raise exceptions in the except block
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        # email = payload.get("sub")
        # if email is None:
        #     raise credentials_exception

        # token_type = payload.get("type")
        # if token_type is None or token_type != type:
        #     raise credentials_exception
        # return email
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e  # do this as a good practice for python to get better info in stacktrace
    except JWTError as e:
        # raise credentials_exception from e
        raise create_credentials_exception("invalid token") from e

    email = payload.get("sub")
    if email is None:
        # raise credentials_exception
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        # raise credentials_exception
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )
    return email


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
        # raise credentials_exception
        raise create_credentials_exception("invalid email or password")
    if not verify_password(password, user.password):
        # raise credentials_exception
        raise create_credentials_exception("invalid email or password")
    return user


""" async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]): simplify by making more modular for the info extraction
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception

        type = payload.get("type")
        if type is None or type != "access":
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e  # do this as a good practice for python to get better info in stacktrace
    except JWTError as e:
        raise credentials_exception from e

    user = await get_user(email=email)
    if user is None:
        raise credentials_exception
    return user """


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    user = await get_user(email=email)
    if user is None:
        # raise credentials_exception
        raise create_credentials_exception("Could not find user for this token")
    return user
