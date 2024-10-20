import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request

from socialapi.database import post_table, database, comments_table
from socialapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from socialapi.models.user import User
from socialapi.security import get_current_user, oauth2_scheme

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Finding post with id {post_id}")

    query = post_table.select().where(post_table.c.id == post_id)

    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
    current_user: Annotated[
        User, Depends(get_current_user)
    ],  # pass callable but don't actually call function for dep injection and value will be injected
):
    logger.info("creating post")
    """ current_user: User = await get_current_user(
        await oauth2_scheme(request)
    )  # Going to grab bearer token from request and pass to get_current_user function, this is how auth jwt works for every request """

    data = post.dict()
    query = post_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    logger.info("Getting all posts")

    query = post_table.select()

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn,
    current_user: Annotated[
        User, Depends(get_current_user)
    ],  # pass callable but don't actually call function for dep injection and value will be injected
):
    logger.info("Creating comment")

    """ current_user: User = await get_current_user(await oauth2_scheme(request)) no longer needed to due dep injection """

    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    data = comment.dict()
    query = comments_table.insert().values(data)

    logger.debug(query)
    # logger.debug(query, extra={"email": "bob@gmail.com"}) if you want to pass extra info to logger

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info("Getting comments on post")

    query = comments_table.select().where(comments_table.c.post_id == post_id)

    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting post and its comments")

    post = await find_post(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
