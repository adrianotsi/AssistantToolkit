import motor.motor_asyncio
from pymongo.errors import ConnectionFailure
import os

class MongoService:
    def __init__(self, default_db_name: str = "watsonAnalyzes"):
        self._client = None
        self._db_name = default_db_name
        self._db = None

    async def connect(self, db_name: str = None):
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
            await self._client.admin.command("ping")
            self._db_name = db_name if db_name else self._db_name
            self._db = self._client[self._db_name]
            return self._db
        except ConnectionFailure as e:
            raise Exception(f"Falha ao conectar: {str(e)}")

    async def get_database(self, db_name: str = None):
        if db_name and (self._db is None or self._db_name != db_name):
            self._db_name = db_name
            self._db = await self.connect(db_name)
        elif self._db is None:
            self._db = await self.connect()
        return self._db

    async def get_collection(self, collection_name: str, db_name: str = None):
        db = await self.get_database(db_name)
        return db[collection_name]

mongo_service_instance = MongoService()