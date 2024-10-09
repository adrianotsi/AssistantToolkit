# Assistant Toolkit
### Overview
AssistantToolkit é uma API desenvolvida com [FastAPI](https://fastapi.tiangolo.com/) que integra o [IBM Discovery](https://www.ibm.com/br-pt/products/watson-discovery) com modelos de linguagem natural (LLMs). A API realiza buscas no IBM Discovery e utiliza os dados obtidos para gerar respostas contextualizadas em chatbots, como o IBM Watson Assistant.

### Instalação
```
pip install -r requirements.txt
```

### Rodando
```
uvicorn main:app --reload
```