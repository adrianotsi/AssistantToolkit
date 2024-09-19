from dotenv import load_dotenv
from fastapi import FastAPI
from services.get_LLMResponse import get_LLMResponse, DiscoveryContext
from services.query_discovery import query_discovery, UserQuery

app = FastAPI(
    title="Assistant Toolkit",
    description="A short API to integrate IBM Discovery plus LLM Models.",
    version="1.0.0"
)

app.openapi_version = "3.0.2"
load_dotenv(override=True)

@app.get("/", tags=["Hello World"], name='its alive?', description='Just a Hello World')
def read_root():
    return {"Hello": "World"}


@app.post("/queryDiscovery/", tags=["Query Search"])
async def queryDiscovery(request: UserQuery):
    print(request)
    res = query_discovery(request.input)
    return res

@app.post("/getLLMResponse/", tags=["LLM"])
async def getLLMResponse(request: DiscoveryContext):
    res = get_LLMResponse(request)
    return res