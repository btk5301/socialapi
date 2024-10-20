import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from socialapi.models.user import UserIn
from socialapi.security import (
    authenticate_user,
    create_access_token,
    get_user,
    get_password_hash,
)
from socialapi.database import database, user_table

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # just an enum, can use status class or number only
            detail="A user with that email already exists",
        )
    # This is a bad idea, passwords stored in plain text
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)

    logger.debug(query)

    await database.execute(query)

    return {"detail": "User created."}


@router.post("/token")
async def login(
    # username: Annotated[str, Form()],
    # password: Annotated[str, Form()],
    # grant_type: Annotated[
    #     str, Form()
    # ],  # replaced old model to follow oauth bearer spec and allow authorization capability in swagger docs
    form_data: Annotated[
        OAuth2PasswordRequestForm, Depends()
    ],  # faster way of doing step above
):
    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}
