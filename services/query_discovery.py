import os
import uuid
from fastapi import HTTPException
from pydantic import BaseModel
import requests

class UserQuery(BaseModel):
    input: str
    projectID: str
    conversationID: str
    
class ResultQuery(BaseModel):
    result: list
    passages_to_show: str
    conversationID: str

def query_discovery(user_query):
    # TODO: Change to IBM Lib
    url = f'{os.getenv("DISCOVERY_ENDPOINT")}/v2/projects/{user_query.projectID}/query'
    params = {
        'version': '2023-03-31'
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.getenv("DISCOVERY_API_KEY")
    }

    payload = {
        'query': user_query.input,
        'natural_language_query': user_query.input,
        'passages':{
            'enable': True,
            'characters': 2000,
            'max_per_document': 2,
            "find_answers": True
        }
    }

    conversationID = user_query.conversationID if user_query.conversationID not in [None, "null"] else str(uuid.uuid4())

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        all_results = []
        passages_to_show_list = []
        data = response.json()

        for result in data.get("results", []):
            document_passages = result.get("document_passages", [])
            document_metadata = result.get("metadata", {})
            document_url = document_metadata.get("source", {}).get("url", "URL não disponível")

            for passage in document_passages:
                passage_text = passage.get("passage_text")
                answers = passage.get("answers", [])
                answer_texts = [answer.get("answer_text") for answer in answers if "answer_text" in answer]

                if passage_text:
                    result_entry = {
                        "passage": passage_text,
                        "url": document_url
                    }

                    if answer_texts:
                        result_entry["answers"] = answer_texts
                        for answer in answer_texts:
                            passages_to_show_list.append(f"[{answer}]({document_url})")

                    all_results.append(result_entry)

        passages_to_show = "\n\n* ".join(passages_to_show_list) if passages_to_show_list else ""
        return {
            "result": all_results,  
            "conversationID": conversationID,
            "passages_to_show": passages_to_show
        }
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))