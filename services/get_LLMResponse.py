import json
import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class LLMContext(BaseModel):
    area: str
    context: str
    question: str
    prompt: str
    messages: str
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

def get_LLMResponse(LLMContext):
    try:
        messages = json.loads(LLMContext.messages)
        prompt = f"""
        {LLMContext.prompt}
        Base de conhecimento: {LLMContext.context}
        ID da conversa: {LLMContext.conversationID}        
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
                    "role": "system",
                    "temperature": 0.5,
                    "content": "Você é um assistente virtual projetado para ajudar atendentes. Siga rigorosamente as instruções abaixo:"
                },
                {
                    "role": "system",
                    "content": "Regras importantes:"
                },
                {
                    "role": "system",
                    "content": "1. Responda apenas com informações contidas na base de conhecimento."
                },
                {
                    "role": "system",
                    "content": "2. NUNCA invente ou crie informações que não estejam documentadas."
                },
                {
                    "role": "system",
                    "content": "3. Se a informação não estiver disponível, informe que não há dados sobre o assunto."
                },
                {
                    "role": "system",
                    "content": "4. Não mencione ou sugira links, a menos que um link válido esteja explicitamente na base de conhecimento."
                },
                {
                    "role": "system",
                    "content": "5. Todas as respostas devem ser em português brasileiro, claras e precisas."
                },
                {
                    "role": "system",
                    "content": "6. Se você fornecer uma resposta fora da base de conhecimento, será considerado inválido e não será aceito."
                },
                {
                    "role": "system",
                    "content": "7. Não mencione NADA fora do contexto da conversa atual identificada pelo ID fornecido. Mantenha todas as respostas e interações estritamente dentro desse contexto."
                },
                {
                    "role": "system",
                    "content": f"Base de conhecimento atualizada: {LLMContext.context}"
                },
                {
                    "role": "assistant",
                    "content": "como posso te ajudar hoje?"
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