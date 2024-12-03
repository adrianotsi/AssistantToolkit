import os
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class LLMContext(BaseModel):
    area: str
    context: list
    question: str
    model: Optional[str] = None
    prompt: str
    messages: list
    conversationID: str

class GenResponse(BaseModel):
    area: str
    question: str
    model: Optional[str] = None
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

def get_LLMResponse(LLMContext, context=None, stream=False):
    try:
        if context is not None:
            conversationID = context['conversationID']
        else:
            conversationID = LLMContext.conversationID

        messages = LLMContext.messages

        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            "model": getattr(LLMContext, 'model', 'llama3.1') or 'llama3.1',
            "stream": stream,
            "options": {
                "num_ctx": 80000,
                "temperature": 0.7
            },
            "messages": [
                {
                    "role": "SYSTEM",
                    "content": f"This conversation is identified by {conversationID}"
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

        response = requests.post(f"{os.getenv('LLAMA_API')}/api/chat", headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        if stream:
            # Gerador para streaming no formato text/event-stream
            def iter_response():
                for chunk in response.iter_content(chunk_size=1024):
                    chunk_decoded = chunk.decode('utf-8').strip()  # Remover espaços ou novas linhas
                    if chunk_decoded:  # Garantir que o chunk tem conteúdo significativo
                        yield f"data: {chunk_decoded}\n\n"


            return iter_response
        else:
            data = response.json()
            if data["message"]["content"]:
                return data
            else:
                raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama: " + str(e))
