from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from app.dependencies import engine, get_db, AsyncSession
import app.models as models
from app.crud import ( create_audio_file, get_audio_files_by_owner, delete_audio_file,
                    create_user, get_user_by_username, delete_user )
from app.schemas import AudioFile, UserCreate, User

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

@app.post("/users/", response_model=User)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await create_user(db, user)
    return db_user

@app.get("/users/{username}", response_model=User)
async def read_user(username: str, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")
async def remove_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}