from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from app.dependencies import engine, get_db, AsyncSession
import app.models as models
from app.crud import ( create_audio_file, get_audio_files_by_owner, delete_audio_file,
                    create_user, get_user_by_username, delete_user, update_user, get_user_by_yandex_id)
from app.schemas import AudioFile, UserCreate, User, Token
from app.auth import oauth2_scheme, authenticate_user, get_current_user, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from urllib.parse import urlencode
import os
import httpx
from fastapi.security import HTTPBearer

# Список допустимых MIME-типов для аудиофайлов
ALLOWED_AUDIO_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/ogg"]

app = FastAPI()
security = HTTPBearer()

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.get("/auth/yandex")
async def yandex_auth():
    # Параметры для запроса к Яндексу
    params = {
        "response_type": "code",
        "client_id": os.getenv("YANDEX_CLIENT_ID"),
        "redirect_uri": os.getenv("YANDEX_REDIRECT_URI"),
    }
    # Формируем URL для авторизации
    auth_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    return {"auth_url": auth_url}

@app.get("/auth/yandex/callback")
async def yandex_callback(code: str, db: AsyncSession = Depends(get_db)):
    # Обмениваем code на access_token у Яндекса
    token_url = "https://oauth.yandex.ru/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": os.getenv("YANDEX_CLIENT_ID"),
        "client_secret": os.getenv("YANDEX_CLIENT_SECRET"),
        "redirect_uri": os.getenv("YANDEX_REDIRECT_URI"),
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to obtain access token from Yandex")

    token_data = response.json()
    access_token = token_data["access_token"]

    # Получаем информацию о пользователе из Яндекса
    user_info_url = "https://login.yandex.ru/info"
    headers = {"Authorization": f"OAuth {access_token}"}
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(user_info_url, headers=headers)
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from Yandex")

    user_info = user_info_response.json()
    yandex_id = user_info["id"]
    username = user_info.get("login", f"user_{yandex_id}")

    # Проверяем, существует ли пользователь в базе данных
    db_user = await get_user_by_yandex_id(db, yandex_id)
    if not db_user:
        # Создаем нового пользователя
        db_user = await create_user(db, UserCreate(username=username))
        db_user.yandex_id = yandex_id
        await db.commit()

    # Создаем JWT-токен для внутренней авторизации
    internal_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": internal_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=10)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/audio/", response_model=AudioFile)
async def upload_audio_file(
    title: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an audio file."
        )
    db_audio_file = await create_audio_file(db, title=title, owner_id=current_user.id)
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
async def delete_user_by_superuser(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only superusers can delete other users")

    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}

@app.put("/users/me", response_model=User)
async def update_current_user(
    new_username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_user = await update_user(db, current_user.id, new_username)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user