from pydantic import BaseModel, Field
from services.mongo_service import MongoService
from pymongo.errors import PyMongoError
from datetime import datetime

class Register(BaseModel):
    area: str
    question: str
    response: str
    feedback: str
    util: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RegisterService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service

    # TODO: improve this service
    async def create_register(self, register):
        try:
            if not register:
                raise ValueError("Um campo está inválido")
            
            db = await self.mongo_service.get_database()

            register['created_at'] = datetime.now()
            register['updated_at'] = datetime.now()
            result = await db["analyzes"].insert_one(register)
            
            if not result.acknowledged:
                raise Exception("A inserção do registro falhou")
            
            return str(result.inserted_id)
        
        except ValueError as ve:
            raise Exception(f"Erro de validação: {str(ve)}")
        
        except PyMongoError as pe:
            raise Exception(f"Erro ao registrar: {str(pe)}")
        
        except Exception as e:
            raise Exception(f"Erro ao criar o registro: {str(e)}")
