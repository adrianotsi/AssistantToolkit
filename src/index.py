from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from services.get_LLMResponse import get_LLMResponse, DiscoveryContext
from services.query_discovery import query_discovery, UserQuery


app = FastAPI(
    title="Assistant Toolkit",
    description="A short API to integrate IBM Discovery plus LLM Models.",
    version="1.0.0"
)

app.openapi_version = "3.0.2"
load_dotenv(override=True)


class ResultQuery(BaseModel):
    result: str 

class Message(BaseModel):
    role: str
    content: str

class LLMResponse(BaseModel):
    model: str
    created_at: str
    message: Message
    done_reason: str
    done: bool
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int

@app.post("/queryDiscovery/", tags=["Query Search"], response_model=ResultQuery)
async def queryDiscovery(request: UserQuery):
    res = query_discovery(request.input)
    return res

@app.post("/getLLMResponse/", tags=["LLM"], response_model=LLMResponse)
async def getLLMResponse(request: DiscoveryContext):
    res = get_LLMResponse(request)
    return res