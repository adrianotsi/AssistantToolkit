import os
import re
import uuid
from fastapi import HTTPException
from pydantic import BaseModel
import requests
import time

class UserQuery(BaseModel):
    input: str
    projectID: str
    conversationID: str

class ResultQuery(BaseModel):
    result: list
    passages_to_show: str
    conversationID: str
    response_time_ns: int

def query_discovery(user_query):

    userInput = sanitize_query_input(user_query.input)
    url = f'{os.getenv("DISCOVERY_ENDPOINT")}/v2/projects/{user_query.projectID}/query'
    params = {
        'version': '2023-03-31'
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': os.getenv("DISCOVERY_API_KEY")
    }

    payload = {
        'query': userInput,
        'natural_language_query': userInput,
        'passages': {
            'enable': True,
            'characters': 2000,
            'max_per_document': 1,
            "find_answers": True
        }
    }

    conversationID = user_query.conversationID if user_query.conversationID not in [None, "null"] else str(uuid.uuid4())

    try:
        start_time_ns = time.perf_counter_ns()

        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()

        end_time_ns = time.perf_counter_ns()
        response_time_ns = end_time_ns - start_time_ns

        all_results = []
        passages_to_show_list = []
        data = response.json()
        document = 1

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
                            passages_to_show_list.append(f"* [{answer}]({document_url})")
                    else:
                        passages_to_show_list.append(f"* [Documento {document}]({document_url})")
                        document += 1

                    all_results.append(result_entry)

        passages_to_show = "\n\n\n".join(passages_to_show_list) if passages_to_show_list else ""
        return {
            "result": all_results,
            "conversationID": conversationID,
            "passages_to_show": passages_to_show,
            "response_time_ns": response_time_ns
        }
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=response.status_code, detail=str(http_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

def sanitize_query_input(user_input):
    return re.sub(r"[^\w\s.,!?'-]", "", user_input)