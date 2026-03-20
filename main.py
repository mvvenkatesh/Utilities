from fastapi import FastAPI
from app.database import engine
from app import db_models
from app.router import router

app = FastAPI()

db_models.Base.metadata.create_all(bind=engine)

app.include_router(router)