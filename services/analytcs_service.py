from fastapi import HTTPException
import pandas as pd
from fastapi.responses import StreamingResponse
import io
from datetime import datetime
from services.mongo_service import MongoService

class AnalytcsService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service
        
    async def analytcs_search(self, start_date, end_date, area, type):
        try:
            start_date_obj = datetime.fromisoformat(start_date)
            end_date_obj = datetime.fromisoformat(end_date)

            collection_name = "analyzesLLM" if type == 'LLMResults' else "analyzes"
            collection = await self.mongo_service.get_collection(collection_name)

            registers = collection.find({
                "area": area,
                "created_at": {
                    "$gte": start_date_obj,
                    "$lte": end_date_obj
                }
            })

            results = []
            async for document in registers:
                results.append(document)

            # Criando o DataFrame com os resultados
            df = pd.DataFrame(results)

            # Gerando o arquivo CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Retornando o arquivo como streaming
            return StreamingResponse(
                iter([csv_buffer.getvalue().encode('utf-8')]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=relatorio.csv"}
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter relatório: {str(e)}")
