from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from services import client_service, mongo_service
from services.analytcs_service import AnalytcsService
from services.auth_service import create_jwt, oauth2_scheme
from services.get_LLMResponse import LLMResponse, get_LLMResponse, LLMContext
from services.query_discovery import ResultQuery, query_discovery, UserQuery
from services.register_service import Register, RegisterLLM, RegisterService

app = FastAPI(
    title="Assistant Toolkit",
    description="An API to integrate IBM Discovery with LLM Models and A.I Assistants.",
    version="2.0.0"
)

app.openapi_version = "3.0.2"
load_dotenv(override=True)

mongo_service = mongo_service.MongoService()

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

@app.post("/getLLMResponse/", 
          tags=["LLM"], 
          name="Gera a resposta no LLM",
          description="Com base no conteúdo encontrado em Query Search e prompt engineering retorna uma resposta gerada no modelo alocado",
          response_model=LLMResponse)
async def getLLMResponse(request: LLMContext, token: str = Depends(oauth2_scheme)):
    res = get_LLMResponse(request)
    return res

@app.get("/healthCheck", 
         tags=['Analyzes'],
         name="Verifica conexão",
         description="Verifica se há conexão com o banco de dados")
async def check_mongo_connection(token: str = Depends(oauth2_scheme)):
    try:
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
    request = request.model_dump()
    register_service = RegisterService(mongo_service)
    register = await register_service.create_register(request)
    return register

# TODO: improve responses and include more validations
@app.post("/createRegisterLLM/", 
          tags=['Analyzes'],
          name="Cria registro: Perguntas + Respostas",
          description="Adiciona o registro das questões, respostas geradas no LLM por operação")
async def createRegisterLL(request: RegisterLLM, token: str = Depends(oauth2_scheme)):
    request = request.model_dump()
    register_service = RegisterService(mongo_service)
    register = await register_service.create_register(request)
    return register

# TODO: improve this service and add exceptions for empty responses
@app.get("/analytcs", 
         tags=['Analyzes'],
         name="Gera relatório: Perguntas + Respostas + Feedback",
         description="Devolve CSV com os registros encontrados conforme query")
async def analytcs(start_date: str = Query(...), end_date: str = Query(...), area: str = Query(...), type: str = Query(...), token: str = Depends(oauth2_scheme)):
    analytcs_service = AnalytcsService(mongo_service)
    analytcs_res = await analytcs_service.analytcs_search(start_date, end_date, area, type)
    return analytcs_res

# TODO: Complete the CRUD flow
@app.post("/createClient", include_in_schema=False)
async def register_client(client: client_service.Client):
    client = client.model_dump()
    result = await client_service.register_client(client['userName'], client['password'], mongo_service)
    return result


@app.post("/get_token", response_model=dict, include_in_schema=False)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    client_data = await client_service.authenticate_client(form_data.username, form_data.password, mongo_service)
    if client_data:
        token = create_jwt({"sub": form_data.username})
        return {"access_token": token}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client ou senha incorretos."
        )