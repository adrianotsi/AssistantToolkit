from datetime import datetime
from pydantic import BaseModel, Field
from pymongo.collection import Collection
from fastapi import HTTPException, status
from passlib.context import CryptContext
from services.mongo_service import MongoService

class Client(BaseModel):
    userName: str
    password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def register_client(userName: str, password: str, mongo_service: MongoService):
    collection = await mongo_service.get_collection("clients")
    if await collection.find_one({"user": userName}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client."
        )
    hashed_password = hash_password(password)
    client_data = {"user": userName, "password": hashed_password}
    await collection.insert_one(client_data)
    return {"message": "New client available"}

async def authenticate_client(userName: str, password: str, mongo_service: MongoService):
    collection = await mongo_service.get_collection("clients")
    client = await collection.find_one({"user": userName})
    if not client or not verify_password(password, client["password"]):
        return False
    return client
