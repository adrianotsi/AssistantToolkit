from datetime import date, datetime
import uuid
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from services import client_service
from services.analytcs_service import AnalytcsService, AreaEnum, TypeEnum
from services.auth_service import create_jwt, oauth2_scheme
from services.embedding_service import embedding_service
from services.get_LLMResponse import ConversationID, GenResponse, LLMResponse, LLMResponseStreaming, get_LLMResponse, LLMContext
from services.query_discovery import ResultQuery, query_discovery, UserQuery
from services.register_service import Register, RegisterLLM, RegisterService
from services.mongo_service import MongoService

app = FastAPI(
    title="Assistant Toolkit",
    description="An API to integrate IBM Discovery with LLM Models and A.I Assistants.",
    version="2.0.2"
)

app.openapi_version = "3.0.2"
load_dotenv(override=True)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.post("/queryDiscovery/", 
          tags=["Query Search"],
          name="Busca conteúdo no IBM Discovery e gera o conversationID", 
          description="Realiza a busca no IBM Discovery, retorna as passagens encontradas e o conversationID", 
          response_model=ResultQuery)
async def queryDiscovery(request: UserQuery, token: str = Depends(oauth2_scheme)):
    res = query_discovery(request)
    return res

@app.get("/getConversationID/", 
          tags=["LLM"], 
          name="Gera um ID para a conversa",
          description="Gera um UUID para a conversa",
          response_model=ConversationID)
async def getConversationID():
    return {'conversationID': str(uuid.uuid4())}

@app.post("/getLLMResponse/",
          tags=["LLM"],
          name="Gera a resposta no LLM",
          description="Com base no conteúdo encontrado em Query Search e prompt engineering retorna uma resposta gerada no modelo alocado",
          response_model=LLMResponse)
async def getLLMResponse(request: LLMContext, token: str = Depends(oauth2_scheme)):
    res = get_LLMResponse(request)
    return res

@app.post("/getLLMResponse/stream",
            tags=["LLM"],
            name="Gera a resposta no LLM via Streaming",
            description="Com base no conteúdo encontrado em Query Search e prompt engineering retorna uma resposta gerada no modelo alocado",
            response_class=LLMResponseStreaming,
            responses = {
                200: {
                    "content": {
                        "text/event-stream": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "string",
                                                "description": "The generated text"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "description": "Stream response with generated text."
                }
            }
        )

async def getLLMResponse(request: LLMContext, token: str = Depends(oauth2_scheme)):
    response_generator = get_LLMResponse(request, stream=True)
    return StreamingResponse(response_generator(), media_type="text/event-stream")

# TODO: Check todos from this service
@app.post("/embedding/")
async def embeding_data():
    res = await embedding_service()
    return res

@app.post("/generateResponse/", 
          tags=["LLM"], 
          name="Buscar conteúdo e gerar resposta",
          description="Busca o conteúdo no IBM DIscovery e retorna uma resposta gerada no modelo alocado",
          response_model=LLMResponse)
async def generateResponse(request: GenResponse, token: str = Depends(oauth2_scheme)):
    discoveryContext = query_discovery(request)
    res = get_LLMResponse(request, discoveryContext)
    return res

@app.get("/healthCheck", 
         tags=['Analyzes'],
         name="Verifica conexão",
         description="Verifica se há conexão com o banco de dados")
async def check_mongo_connection(token: str = Depends(oauth2_scheme)):
    try:
        async with MongoService() as mongo_service:
            await mongo_service.connect()
            return {"status": "Conexão bem-sucedida!"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# TODO: improve responses and include more validations
@app.post("/createRegister/", 
          tags=['Analyzes'],
          name="Cria registro: Perguntas + Respostas + Feedback",
          description="Adiciona o registro das questões, respostas e avaliações por operação")
async def createRegister(request: Register, token: str = Depends(oauth2_scheme)):
    async with MongoService() as mongo_service:
        register_service = RegisterService(mongo_service)
        register = await register_service.create_register(request.model_dump())
        return register

# TODO: improve responses and include more validations
@app.post("/createRegisterLLM/", 
          tags=['Analyzes'],
          name="Cria registro: Perguntas + Respostas",
          description="Adiciona o registro das questões, respostas geradas no LLM por operação")
async def createRegisterLL(request: RegisterLLM, token: str = Depends(oauth2_scheme)):
    async with MongoService() as mongo_service:
        register_service = RegisterService(mongo_service)
        register = await register_service.create_register(request.model_dump())
        return register

# TODO: improve this service and add exceptions for empty responses
@app.get("/analytcs", 
         tags=['Analyzes'],
         name="Gera relatório: Perguntas + Respostas + Feedback",
         description="Devolve CSV com os registros encontrados conforme query")
async def analytcs(start_date: date = Query(..., description="Buscar a partir de", example="2024-01-01"), end_date: date = Query(..., description="Buscar até", example="2024-01-01"), area: AreaEnum = Query(...), type: TypeEnum = Query(...), token: str = Depends(oauth2_scheme)):
    async with MongoService() as mongo_service:
        analytcs_service = AnalytcsService(mongo_service)
        analytcs_res = await analytcs_service.analytcs_search(start_date, end_date, area, type)
        return analytcs_res

# TODO: Complete the CRUD flow
@app.post("/createClient", include_in_schema=False)
async def register_client(client: client_service.Client):
    client = client.model_dump()
    result = await client_service.register_client(client['userName'], client['password'])
    return result


@app.post("/get_token", response_model=dict, 
         tags=['Login'],
         name="Gera token",
         description="Gera o token JWT utilizando para autenticação")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
   async with MongoService() as mongo_service:
        client_data = await client_service.authenticate_client(form_data.username, form_data.password)
        if client_data:
            token = create_jwt({"sub": form_data.username})
            return {"access_token": token}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client ou senha incorretos."
            )