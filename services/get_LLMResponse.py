import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class DiscoveryContext(BaseModel):
    context: object
    question: str

def get_LLMResponse(discovery_context):
    prompt = f"{discovery_context.context}\n\nUsuário: {discovery_context.question}\nAI:"

    headers = {
        'Content-Type': 'application/json'
    }

    payload = { 
        "model": "llama3.1",
        "prompt": prompt,
        "stream":False
    }

    try:
        response = requests.post(os.getenv("LLAMA_API_ENDPOINT"), headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        if 'text' in data:
            return data['text']
        elif 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['text']
        else:
            return ''
    except requests.exceptions.RequestException as e:
        print('Erro ao chamar a API do Llama:', e)
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama")