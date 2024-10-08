import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class DiscoveryContext(BaseModel):
    area: str
    context: str
    question: str

def get_LLMResponse(discovery_context):

    if(discovery_context.area == 'sac'):
        prompt = f"""
            You are a virtual assistant designed to assist agents during a customer service operation (SAC).
            Your primary role is to instruct the agent on how to offer efficient solutions to meet the customer’s needs and resolve their requests or issues proactively and thoroughly.
            When a customer presents a question, request, or complaint, guide the agent to provide clear answers, propose appropriate alternatives, and solve the issue effectively, always based on the provided knowledge base.
            You must not invent or create any information outside of the knowledge base {discovery_context.context}.
            Whenever possible, provide detailed instructions on how the agent should handle the conversation, ensuring empathetic and professional communication.
            All responses must be provided in Brazilian Portuguese.
            """
    else:
        prompt = f"""
            You are a virtual assistant designed to assist agents during a customer retention operation. 
            Your primary role is to instruct the agent on how to retain the customer by offering all possible retention strategies. 
            When a customer expresses the desire to cancel their plan, guide the agent to propose alternative offers or solutions to prevent cancellation. 
            Only if the customer rejects all retention attempts should the agent proceed with logging the cancellation reason. 
            Always provide the agent with specific instructions on what to say and do. Do not speak directly to the customer. 
            Instead, instruct the agent on how to approach the conversation and retain the customer as much as possible. 
            All responses must always be provided in **Brazilian Portuguese**. 
            This is your knowledgebase: {discovery_context.context}.
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
                "content": prompt
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