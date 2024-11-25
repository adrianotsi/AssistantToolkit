from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os

class MongoService:
    def __init__(self, default_db_name: str = "watsonAnalyzes"):
        self._client = None
        self._db_name = default_db_name
        self._db = None

    async def connect(self, db_name: str = None):
        try:
            self._client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
            await self._client.admin.command("ping")
            self._db_name = db_name if db_name else self._db_name
            self._db = self._client[self._db_name]
            return self._db
        except ConnectionFailure as e:
            raise Exception(f"Falha ao conectar: {str(e)}")

    async def disconnect(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def get_database(self, db_name: str = None):
        if db_name and (self._db is None or self._db_name != db_name):
            self._db_name = db_name
            self._db = await self.connect(db_name)
        elif self._db is None:
            self._db = await self.connect()
        return self._db

    async def get_collection(self, collection_name: str, db_name: str = None):
        # Obtém o banco de dados e retorna a coleção especificada
        db = await self.get_database(db_name)
        return db[collection_name]

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
