import os
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class DiscoveryContext(BaseModel):
    context: object
    question: str

def get_LLMResponse(discovery_context):

    headers = {
        'Content-Type': 'application/json'
    }

    payload = { 
        "model": "llama3.1",
        "prompt": f"""
                    You are a virtual assistant designed to assist agents during a customer retention operation. 
                    Your primary role is to instruct the agent on how to retain the customer by offering all possible retention strategies. 
                    When a customer expresses the desire to cancel their plan, guide the agent to propose alternative offers or solutions to prevent cancellation. 
                    Only if the customer rejects all retention attempts should the agent proceed with logging the cancellation reason. 
                    Always provide the agent with specific instructions on what to say and do. Do not speak directly to the customer. 
                    Instead, instruct the agent on how to approach the conversation and retain the customer as much as possible. 
                    All responses must always be provided in **Brazilian Portuguese**. 
                    This is your knowledgebase: {discovery_context.context}.
                    This is the question from agent: {discovery_context.question}""",
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