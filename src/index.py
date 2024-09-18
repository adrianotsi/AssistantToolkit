from typing import Union
from dotenv import load_dotenv
from fastapi import FastAPI
from services.get_LLMResponse import get_LLMResponse, DiscoveryContext
from services.query_discovery import query_discovery, UserQuery

app = FastAPI()
load_dotenv()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/queryDiscovery/")
async def queryDiscovery(request: UserQuery):
    print(request)
    res = query_discovery(request.input)
    return res

@app.post("/getLLMResponse/")
async def getLLMResponse(request: DiscoveryContext):
    res = get_LLMResponse(request)
    return res