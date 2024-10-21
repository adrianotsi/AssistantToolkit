import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class DiscoveryContext(BaseModel):
    area: str
    context: str
    question: str
    prompt: str

def get_LLMResponse(discovery_context):

    prompt = f"""
            {discovery_context.prompt}
            Base de conhecimento: {discovery_context.context}
            """

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "model": "llama3.1",
        "stream": False,
        "messages": [
            {
                "role": "system",
                "temperature": 10,
                "content": prompt
            },
            {
                "role": "assistant",
                "content": "como posso te ajudar hoje?"
            },
            {
                "role": "user",
                "content": discovery_context.question
            }
        ]
    }

    try:
        response = requests.post(f"{os.getenv("LLAMA_API")}/api/chat", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if data["message"]["content"]:
            return data
        else:
            raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama" + str(e))