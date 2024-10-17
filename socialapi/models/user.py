from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    email: str


class UserIn(User):
    password: str  # reverse of user model since we don't want to return password
