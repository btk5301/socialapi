import logging
from fastapi import APIRouter, HTTPException

from socialapi.database import post_table, database, comments_table
from socialapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Finding post with id {post_id}")

    query = post_table.select().where(post_table.c.id == post_id)

    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    logger.info("creating post")

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
async def create_comment(comment: CommentIn):
    logger.info("Creating comment")

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
