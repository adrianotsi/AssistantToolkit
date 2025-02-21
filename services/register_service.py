from pydantic import BaseModel, Field
from services.mongo_service import MongoService
from pymongo.errors import PyMongoError
from datetime import datetime

class Register(BaseModel):
    area: str
    question: str
    response: str
    response_time: int
    feedback: str
    response_time: int ## Tempo total 
    eval_duration: int ## Tempo gerando resposta
    load_time: int ## Tempo de carregamento do modelo
    prompt_tokens: int ## Tokens no prompt
    prompt_eval_time: int ## Tempo avaliando prompt
    response_tokens: int ## Tokens na resposta
    query_time: int
    util: str
    retry: bool
    nomeColaborador: str
    matriculaColaborador: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RegisterLLM(BaseModel):
    area: str
    question: str
    response: str
    response_time: int ## Tempo total 
    eval_duration: int ## Tempo gerando resposta
    load_time: int ## Tempo de carregamento do modelo
    prompt_tokens: int ## Tokens no prompt
    prompt_eval_time: int ## Tempo avaliando prompt
    response_tokens: int ## Tokens na resposta
    query_time: int
    retry: bool
    nomeColaborador: str
    matriculaColaborador: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RegisterService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service

    async def create_register(self, register):
        try:
            if not register:
                raise ValueError("Um campo está inválido")
            
            async with self.mongo_service as mongo:
                db = await mongo.get_database()

                register['created_at'] = datetime.now()
                register['updated_at'] = datetime.now()
                if 'feedback' not in register:
                    result = await db["analyzesLLM"].insert_one(register)
                else:
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
