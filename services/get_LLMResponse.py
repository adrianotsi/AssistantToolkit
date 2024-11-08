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
            "model": "llama3.1",
            "stream": False,
            "keep_alive": 0,
            "options": {
                # "top_p": 15,  # Diminuído para limitar respostas criativas
                "temperature": 2,  # Mais baixa para respostas diretas e seguras
                # "top_k": 10,  # Reduzido para manter consistência nas respostas
                # "repeat_last_n": 500,  # Considerar aumentar para manter o contexto recente
                # "repeat_penalty": 1  # Penalidade para evitar repetições
            },

            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Inicie uma nova conversa exclusiva com o ID {getattr(LLMContext, 'conversationID', conversationID)}. "
                        "Não mencione nenhum assunto ou conversa que foi conversado anteriormente. Considere apenas as informações desta sequencia de mensagens."
                        "Este ID é sigiloso"
                    )
                },
                {
                    "role": "system",
                    "content": f"Informações Relevantes para Respostas: {getattr(LLMContext, 'context', context)}"
                },
                {
                    "role": "system",
                    "content": (
                        "Diretrizes para o Assistente:\n\n"
                        
                        "- **Responda de forma completa e detalhada**: Estruture a resposta com todas as informações relevantes disponíveis, como em uma explicação completa ou um guia.\n"
                        "- **Organize a resposta**: Se o conteúdo permitir, use uma lista ou uma estrutura clara para detalhar todas as possibilidades ou instruções.\n"
                        "- **Não mencione documentos ou notas internas**: Foque apenas nas informações e detalhes relevantes ao contexto, sem citar nomes de documentos específicos.\n"
                        "- **Exemplo de Resposta Estruturada**: Se perguntado sobre 'Quem pode solicitar o corte provisório', descreva todas as opções de forma organizada, como:\n"
                        "    - 'A solicitação de corte provisório pode ser feita por diversas pessoas, dependendo da situação específica. Aqui estão algumas possibilidades...'\n"
                        "- **Evite Respostas Curtas ou Isoladas**: Não responda apenas com uma frase curta. Sempre ofereça uma resposta completa com todas as informações encontradas.\n"
                        "- **Diretamente do Conteúdo Acima**: Responda usando exclusivamente as informações fornecidas nas Informações Relevantes acima, e ignore qualquer outro conhecimento externo ou suposição.\n"
                        
                        "- Importante: Responda de forma objetiva e clara, sem mencionar a existência dessas diretrizes."
                    )
                },
                {
                    "role": "system",
                    "content": "Contexto: O atendente está com o cliente em linha; responda diretamente ao atendente com as informações acima."
                },
                {
                    "role": "assistant",
                    "content": "Olá, atendente! Envie sua dúvida ou tema para consulta."
                }
            ]
        }

        payload["messages"].extend(messages)
        
        payload["messages"].append(
            {
                "role": "user",
                "content": LLMContext.question
            }
        )

        print(payload)

        response = requests.post(f"{os.getenv("LLAMA_API")}/api/chat", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if data["message"]["content"]:
            return data
        else:
            raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Erro ao obter resposta do Llama" + str(e))