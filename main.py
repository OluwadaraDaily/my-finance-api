# FastAPI app entry point

from fastapi import FastAPI
from api.v1.endpoints import auth_router
from db.session import engine
from db.base import Base
from db.models import *  # This imports all models

app = FastAPI()

app.include_router(auth_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)