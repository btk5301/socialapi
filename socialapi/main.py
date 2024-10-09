from fastapi import FastAPI

from socialapi.routers.post import router as post_roouter

app = FastAPI()

app.include_router(post_roouter)
