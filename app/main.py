from fastapi import FastAPI
from app.dependencies import engine
import app.models as models

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
