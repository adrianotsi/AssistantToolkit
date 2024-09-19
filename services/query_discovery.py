import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class UserQuery(BaseModel):
    input: str

def query_discovery(user_query):
    # TODO: Change to IBM Lib and get document passages 
    url = f'{os.getenv("DISCOVERY_ENDPOINT")}/v2/projects/{os.getenv("PROJECT_ID")}/query'
    params = {
        'version': '2023-03-31'  # Verifique a versão correta da API
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.getenv("DISCOVERY_API_KEY")
    }

    payload = {
        'query': user_query,
        'natural_language_query': user_query,
        'passages':{
            'characters': 30000
        }
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["results"][0]['document_passages'][0]['passage_text'] + data["results"][1]['document_passages'][0]['passage_text']
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))