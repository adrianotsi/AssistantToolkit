import json
import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class LLMContext(BaseModel):
    area: str
    context: dict
    question: str
    prompt: str
    messages: list
    conversationID: str

class GenResponse(BaseModel):
    area: str
    question: str
    model: str
    prompt: str
    messages: list
    input: str
    projectID: str
    conversationID: str

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

class ConversationID(BaseModel):
    conversationID: str

def get_LLMResponse(LLMContext, context=None):
    try:
        if context != None:
            conversationID = context['conversationID']
        messages = LLMContext.messages

        headers = {
            'Content-Type': 'application/json'
        }   

        payload = {
            "model": f"{getattr(LLMContext, 'model', 'llama3.1')}",
            "stream": False,
            # "keep_alive": 0,
            "options": {
                "num_ctx": 80000,
                # "top_p": 0.7,  # Diminuído para limitar respostas criativas
                "temperature": 0.7,  # Mais baixa para respostas diretas e seguras
                # "repeat_penalty": 0.5  # Penalidade para evitar repetições
            },

            "messages": [
                {
                    "role": "SYSTEM",
                    "content": f"This conversation is identified by {getattr(LLMContext, 'conversationID', conversationID)}"
                },
                {
                    "role": "SYTEM",
                    "content": "You must strictly adhere to this identifier and avoid referencing or mentioning information from conversations with different identifiers."
                },
                {
                    "role": "SYSTEM",
                    "content": f"Now this is your knowledge base: {getattr(LLMContext, 'context', context)}"
                }
            ]
        }

        payload["messages"].extend(messages)
        
        payload["messages"].append(
            {
                "role": "USER",
                "content": LLMContext.question
            }
        )

        print(payload)

        response = requests.post(f"{os.getenv("LLAMA_API")}/api/chat", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        print(response)
        if data["message"]["content"]:
            return data
        else:
            raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama" + str(e))