import os
import uuid
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class UserQuery(BaseModel):
    input: str
    projectID: str
    conversationID: str
    
class ResultQuery(BaseModel):
    result: str 
    conversationID: str

def query_discovery(user_query):
    # TODO: Change to IBM Lib and get document passages 
    url = f'{os.getenv("DISCOVERY_ENDPOINT")}/v2/projects/{user_query.projectID}/query'
    params = {
        'version': '2023-03-31'  # Verifique a versão correta da API
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.getenv("DISCOVERY_API_KEY")
    }

    payload = {
        'query': user_query.input,
        'natural_language_query': user_query.input,
        'passages':{
            'characters': 30000
        }
    }

    conversationID = user_query.conversationID if user_query.conversationID not in [None, "null"] else str(uuid.uuid4())

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        all_passages = ''
        data = response.json()

        for result in data.get("results", []):
            document_passages = result.get("document_passages", [])
            for passage in document_passages:
                passage_text = passage.get("passage_text")
                if passage_text:
                    all_passages += passage_text + "\n"

        return {
            "result": all_passages,
            "conversationID": conversationID
        }
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))