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
        'natural_language_query': user_query
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))