import os
import ollama
import chromadb

## TODO: Add parameters to request, abstract some functions
async def embedding_service():
    documents =   []
    ## TODO: Add persist to chromaDB
    client = chromadb.Client()
    clientOllama = ollama.Client(
        host= os.getenv('LLAMA_API'),
        headers={'Content-Type': 'application/json'}
    )

    # TODO: Change create to get_or_create 
    # client.delete_collection(name="docs")
    collection = client.create_collection(name="docs")


    for i, doc in enumerate(documents):
        passage = doc.get("passage", "")
        answers = " ".join(doc.get("answers", []))
        url = doc.get("url", "")
        
        prompt = f"{passage}\n{answers}\n{url}"

        response = clientOllama.embeddings(model="nomic-embed-text", prompt=prompt)
        embedding = response["embedding"]

        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[prompt], 
        )

    # TODO: Remove and add prompt by parameter
    prompt = ''

    # generate an embedding for the prompt and retrieve the most relevant doc
    # TODO: Add model by parameter
    response = clientOllama.embeddings(
        prompt=prompt,
        model="nomic-embed-text"
    )
    results = collection.query(
    query_embeddings=[response["embedding"]],
    n_results=10
    )
    data = results['documents']
    print("resultado do embedding:")
    print(data)


    # TODO: Remove this part from code, duplicated function
    messagesArray = [
            {
                "role": "system",
                "content": f"This conversation is identified by 013456"
            },
            {
                "role": "system",
                "content": "You must strictly adhere to this identifier and avoid referencing or mentioning information from conversations with different identifiers."
            },
            {
                "role": "system",
                "content": f"Now this is your knowledge base: {data}"
            }
        ]
    
    messagesArray.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    print(messagesArray)
    response = clientOllama.chat(
        model= 'llamaEnel-instruct-q4_K_M',
        options= {             
            "num_ctx": 80000,
            "temperature": 0.7
        },
        messages=messagesArray
    )

    return response