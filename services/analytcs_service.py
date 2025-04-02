from enum import Enum
from fastapi import HTTPException
import pandas as pd
from fastapi.responses import StreamingResponse
import io
from datetime import datetime, timezone, timedelta, time
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
            # Se start_date/end_date não forem datetime, converte-os usando datetime.combine.
            if not isinstance(start_date, datetime):
                start_date_obj = datetime.combine(start_date, time.min)
            else:
                start_date_obj = start_date

            if not isinstance(end_date, datetime):
                end_date_obj = datetime.combine(end_date, time.min)
            else:
                end_date_obj = end_date

            # Ajustar para UTC e definir start_date_obj como o começo do dia
            start_date_obj = start_date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            # Definir end_date_obj como o começo do dia e depois somar 1 dia para que a query use $lt
            end_date_obj = end_date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc) + timedelta(days=1)

            print(f"Start Date (UTC): {start_date_obj}")
            print(f"End Date (UTC): {end_date_obj}")

            collection_llm = await self.mongo_service.get_collection("analyzesLLM")
            collection_legacy = await self.mongo_service.get_collection("analyzes")

            query_filter = {
                "area": area.value if isinstance(area, AreaEnum) else area,
                "created_at": {
                    "$gte": start_date_obj,
                    "$lt": end_date_obj  # Usamos $lt para capturar até o início do próximo dia
                }
            }

            print(f"Query: {query_filter}")

            registers_llm = collection_llm.find(query_filter)
            registers_legacy = collection_legacy.find(query_filter)

            results_llm = [doc async for doc in registers_llm]
            results_legacy = [doc async for doc in registers_legacy]

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