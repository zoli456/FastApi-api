from fastapi import FastAPI
from contextlib import asynccontextmanager
from db import database, metadata, engine
from routes import auth, users, admin, messages

metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admin.router, prefix="/admin", tags=["Admins"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])
