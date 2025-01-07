from enum import Enum
from fastapi import HTTPException
import pandas as pd
from fastapi.responses import StreamingResponse
import io
from datetime import datetime
from services.mongo_service import MongoService

class AreaEnum(str, Enum):
    enel = "enel"
    retenção = "retenção"
    sac = "sac"

class AnalytcsService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service

    async def analytcs_search(self, start_date, end_date, area):
        try:
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat() 
            start_date_obj = datetime.fromisoformat(start_date_str)
            end_date_obj = datetime.fromisoformat(end_date_str)

            collection_llm = await self.mongo_service.get_collection("analyzesLLM")
            collection_legacy = await self.mongo_service.get_collection("analyzes")

            registers_llm = collection_llm.find({
                "area": area,
                "created_at": {
                    "$gte": start_date_obj,
                    "$lte": end_date_obj
                }
            })

            registers_legacy = collection_legacy.find({
                "area": area,
                "created_at": {
                    "$gte": start_date_obj,
                    "$lte": end_date_obj
                }
            })

            results_llm = []
            async for document in registers_llm:
                results_llm.append(document)

            results_legacy = []
            async for document in registers_legacy:
                results_legacy.append(document)

            # Verifica se há resultados
            if not results_llm and not results_legacy:
                raise HTTPException(status_code=404, detail="Nenhum registro encontrado para os critérios fornecidos.")

            # Criando DataFrames
            df_llm = pd.DataFrame(results_llm)
            df_legacy = pd.DataFrame(results_legacy)

            # Preencher a coluna "util" e "feedback" com "N/A" para resultados da collection de respostas do LLM
            if "util" not in df_llm.columns:
                df_llm["util"] = "N/A"
            if "feedback" not in df_llm.columns:
                df_llm["feedback"] = "N/A"

            # Concatenar os DataFrames 
            df_combined = pd.concat([df_llm, df_legacy], ignore_index=True)

            # Remover duplicatas com base em "question" e "response", priorizando registros de "analyzes" (registro com feeback)
            df_combined = df_combined.sort_values(by=["created_at"], ascending=False)
            df_combined = df_combined.drop_duplicates(subset=["question", "response"], keep="first")

            # Transformando campos de nanosegundos para segundos
            for column in ['response_time', 'eval_duration', 'load_time', 'prompt_eval_time', 'query_time']:
                if column in df_combined.columns:
                    df_combined[column] = pd.to_numeric(df_combined[column], errors='coerce') 
                    df_combined[column] = (df_combined[column] / 1_000_000_000).apply(lambda x: round(x, 2) if pd.notnull(x) else x)

            # Gerando o arquivo Excel
            excel_buffer = io.BytesIO()
            df_combined.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)

            # Retornando o arquivo como streaming
            return StreamingResponse(
                iter([excel_buffer.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=relatorio.xlsx"}
            )
        
        except HTTPException as e:
            raise e  # Relança exceções HTTP específicas

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter relatório: {str(e)}")