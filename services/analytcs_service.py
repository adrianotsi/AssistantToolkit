from fastapi import HTTPException
import pandas as pd
from fastapi.responses import StreamingResponse
import io
from datetime import datetime
from services.mongo_service import MongoService

class AnalytcsService:
    def __init__(self, mongo_service: MongoService):
        self.mongo_service = mongo_service
        
    async def analytcs_search(self, start_date, end_date, area):
        try:
            start_date_obj = datetime.fromisoformat(start_date)
            end_date_obj = datetime.fromisoformat(end_date)


            db = await self.mongo_service.get_database()
            collection = db.analyzes  

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

            # Criação de um DataFrame
            df = pd.DataFrame(results)

            # Gerar CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Retornar como streaming
            return StreamingResponse(
                iter([csv_buffer.getvalue().encode('utf-8')]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=relatorio.csv"}
            )
        
        except:
            raise HTTPException(status_code= 500, detail="Erro ao obter relatório")
