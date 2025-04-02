from pydantic import BaseModel, Field
from services.mongo_service import MongoService
from pymongo.errors import PyMongoError
from datetime import datetime, timezone

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

    async def create_register(self, register: dict):
        try:
            if not isinstance(register, dict) or not register:
                raise ValueError("Os dados do registro são inválidos.")

            async with self.mongo_service as mongo:
                db = await mongo.get_database()

                # Se os timestamps forem strings, converter corretamente para UTC
                for field in ["created_at", "updated_at"]:
                    if field in register and isinstance(register[field], str):
                        dt = datetime.fromisoformat(register[field])
                        if dt.tzinfo is None:  # Se não tem timezone, assumir UTC
                            dt = dt.replace(tzinfo=timezone.utc)
                        register[field] = dt

                # Caso os campos não sejam enviados, definir UTC atual
                register.setdefault("created_at", datetime.now(timezone.utc))
                register.setdefault("updated_at", datetime.now(timezone.utc))

                # Escolher a coleção correta com base na presença do campo 'feedback'
                collection_name = "analyzesLLM" if "feedback" not in register else "analyzes"
                result = await db[collection_name].insert_one(register)

                if not result.acknowledged:
                    raise Exception("A inserção do registro falhou.")

                return str(result.inserted_id)

        except ValueError as ve:
            raise Exception(f"Erro de validação: {str(ve)}")

        except PyMongoError as pe:
            raise Exception(f"Erro ao registrar no banco de dados: {str(pe)}")

        except Exception as e:
            raise Exception(f"Erro ao criar o registro: {str(e)}")