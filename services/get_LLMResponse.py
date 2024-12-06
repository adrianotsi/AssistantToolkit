import os
from typing import Optional
from fastapi import HTTPException, Response
from pydantic import BaseModel
from ollama import Client
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

class LLMResponseStreaming(Response):
    media_type = "text/event-stream"

class ConversationID(BaseModel):
    conversationID: str

def get_LLMResponse(LLMContext, context=None, stream=False):
    try:
        ## Define client do Ollama
        clientOllama = Client(
            host= os.getenv('LLAMA_API'),
            headers={'Content-Type': 'application/json'}
        )

        ## Verifica se os resultados do Discovery vieram de gerateResponse ou getLLMresponse
        if context is not None:
            conversationID = context['conversationID']
        else:
            conversationID = LLMContext.conversationID

        ## Array de toda a conversa atual
        messages = LLMContext.messages

        ## Define payload
        messagesArray = [
                {
                    "role": "system",
                    "content": f"This conversation is identified by {conversationID}"
                },
                {
                    "role": "system",
                    "content": "You must strictly adhere to this identifier and avoid referencing or mentioning information from conversations with different identifiers."
                },
                {
                    "role": "system",
                    "content": f"Now this is your knowledge base: {getattr(LLMContext, 'context', context)}"
                }
            ]
        
        ## Add conversa atual ao payload
        messagesArray.extend(messages)

        ## Add mensagem atual ao payload
        messagesArray.append(
            {
                "role": "user",
                "content": LLMContext.question
            }
        )

        ## Log payload 
        print(messagesArray)
        ## Requisição ao Ollama
        response = clientOllama.chat(
            model= getattr(LLMContext, 'model', 'llama3.1') or 'llama3.1',
            stream= stream,
            options= {             
                "num_ctx": 80000,
                "temperature": 0.7
            },
            messages=messagesArray
        )
        print(type(response))

        
        if stream:
            def iter_response():
                for part in response:  # Itera sobre o gerador
                    # Acessa o conteúdo dentro de 'message' -> 'content'
                    chunk_decoded = part.get('message', {}).get('content', '').strip()
                    if chunk_decoded:  # Verifica se há conteúdo válido
                        yield f"data: {chunk_decoded}\n\n"
            return iter_response
        elif response:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama: " + str(e))
