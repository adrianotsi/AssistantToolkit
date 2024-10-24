from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from services import mongo_service
from services.analytcs_service import AnalytcsService
from services.get_LLMResponse import LLMResponse, get_LLMResponse, LLMContext
from services.query_discovery import ResultQuery, query_discovery, UserQuery
from services.register_service import Register, RegisterService

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

@app.post("/queryDiscovery/", tags=["Query Search"], response_model=ResultQuery)
async def queryDiscovery(request: UserQuery):
    res = query_discovery(request)
    return res

@app.post("/getLLMResponse/", tags=["LLM"], response_model=LLMResponse)
async def getLLMResponse(request: LLMContext):
    res = get_LLMResponse(request)
    return res

@app.get("/healthCheck", tags=['Analyzes'])
async def check_mongo_connection():
    try:
        await mongo_service.connect()
        return {"status": "Conexão bem-sucedida!"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# TODO: improve responses 
@app.post("/createRegister/", tags=['Analyzes'])
async def createRegister(request: Register):
    request = request.model_dump()
    register_service = RegisterService(mongo_service)
    register = await register_service.create_register(request)
    return register

# TODO: improve this service and add exceptions for empty responses
@app.get("/analytcs", tags=['Analyzes'])
async def analytcs(start_date: str = Query(...), end_date: str = Query(...), area: str = Query(...)):
    analytcs_service = AnalytcsService(mongo_service)
    analytcs_res = await analytcs_service.analytcs_search(start_date, end_date, area)
    return analytcs_res