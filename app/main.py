from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from app.dependencies import engine, get_db, AsyncSession
import app.models as models
from app.crud import create_audio_file, get_audio_files_by_owner, delete_audio_file
from app.schemas import AudioFile

# Список допустимых MIME-типов для аудиофайлов
ALLOWED_AUDIO_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/ogg"]

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.post("/audio/", response_model=AudioFile)
async def upload_audio_file(
    title: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # Временно используем фиксированного пользователя
):
    if file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an audio file."
        )
    db_audio_file = await create_audio_file(db, title=title, owner_id=owner_id)
    file_path = db_audio_file.path
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return db_audio_file

@app.get("/audio/", response_model=list[AudioFile])
async def list_audio_files(owner_id: int = 1, db: AsyncSession = Depends(get_db)):
    return await get_audio_files_by_owner(db, owner_id)

@app.delete("/audio/{audio_file_id}")
async def delete_audio(audio_file_id: int, db: AsyncSession = Depends(get_db), owner_id: int = 1):
    success = await delete_audio_file(db, audio_file_id, owner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return {"detail": "Audio file deleted"}