import json
import os
from typing import Optional
from fastapi import HTTPException, Response
from pydantic import BaseModel
from ollama import Client

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

class LLMResponseDefinitions:
    responses = {
    200: {
        "content": {
            "text/event-stream": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The generated text"
                                },
                                "model": {
                                    "type": "string",
                                    "description": "The model used for generating the response"
                                },
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Timestamp when the response was created"
                                },
                                "done_reason": {
                                    "type": "string",
                                    "description": "Reason why the operation is completed"
                                },
                                "done": {
                                    "type": "boolean",
                                    "description": "Indicates whether the operation is completed"
                                },
                                "total_duration": {
                                    "type": "integer",
                                    "description": "Total time duration for the operation (in milliseconds)"
                                },
                                "load_duration": {
                                    "type": "integer",
                                    "description": "Duration for loading the model (in milliseconds)"
                                },
                                "prompt_eval_count": {
                                    "type": "integer",
                                    "description": "Number of times the prompt was evaluated"
                                },
                                "prompt_eval_duration": {
                                    "type": "integer",
                                    "description": "Total duration for prompt evaluation (in milliseconds)"
                                },
                                "eval_count": {
                                    "type": "integer",
                                    "description": "Number of evaluations performed"
                                },
                                "eval_duration": {
                                    "type": "integer",
                                    "description": "Total duration of evaluations (in milliseconds)"
                                }
                            }
                        }
                    }
                }
            }
        },
        "description": "Stream response with generated text and additional LLM response data."
    }
}


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

        
        if stream:
            def iter_response():
                for part in response:  
                    chunk_decoded = part.get('message', {}).get('content', '')
                    # if chunk_decoded:
                    response_data = {
                        'message': chunk_decoded or '',
                        'model': part.get('model', ''),
                        'created_at': part.get('created_at', ''),
                        'done_reason': part.get('done_reason', ''),
                        'done': part.get('done', False),
                        'total_duration': part.get('total_duration', 0),
                        'load_duration': part.get('load_duration', 0),
                        'prompt_eval_count': part.get('prompt_eval_count', 0),
                        'prompt_eval_duration': part.get('prompt_eval_duration', 0),
                        'eval_count': part.get('eval_count', 0),
                        'eval_duration': part.get('eval_duration', 0)
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"
            return iter_response
        elif response:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama: " + str(e))
