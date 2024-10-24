import motor.motor_asyncio
from pymongo.errors import ConnectionFailure
import os


# TODO: improve this service
class MongoService:
    def __init__(self):
        self._client = None
        self._db = None

    async def connect(self):
        if not self._client:
            try:
                self._client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URL"])
                await self._client.admin.command("ping")
                self._db = self._client.watsonAnalyzes
                return self._db
            except ConnectionFailure as e:
                raise Exception(f"Falha ao conectar: {str(e)}")

    async def get_database(self):
        if self._db is None:
            # Conectar ao banco de dados aqui
            self._db = await self.connect()  # Exemplo de conexão
        return self._db
