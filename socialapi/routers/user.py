import logging
from fastapi import APIRouter, HTTPException, status

from socialapi.models.user import UserIn
from socialapi.security import get_user
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
    query = user_table.insert().values(email=user.email, password=user.password)

    logger.debug(query)

    await database.execute(query)

    return {"detail": "User created."}
