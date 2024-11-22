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
    result: dict 
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
            'enable': True,
            'characters': 2000,
            'max_per_document': 2
        }
    }

    conversationID = user_query.conversationID if user_query.conversationID not in [None, "null"] else str(uuid.uuid4())

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        all_results = {}  
        data = response.json()

        result_index = 1  

        for result in data.get("results", []):
            document_passages = result.get("document_passages", [])
            document_metadata = result.get("metadata", {})
            document_url = document_metadata.get("source", {}).get("url", "URL não disponível")

            for passage in document_passages:
                passage_text = passage.get("passage_text")
                if passage_text:
                    all_results[f"passage_{result_index}"] = {
                        "text": passage_text,
                        "url": document_url
                    }
                    result_index += 1

        return {
            "result": all_results, 
            "conversationID": conversationID
        }
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))