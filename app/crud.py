from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AudioFile, User
from app.schemas import UserCreate
import os
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_audio_file(db: AsyncSession, title: str, owner_id: int):
    file_path = f"storage/{owner_id}/{title}"  # Путь для хранения файла
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Создаем директорию, если её нет
    db_audio_file = AudioFile(title=title, path=file_path, owner_id=owner_id)
    db.add(db_audio_file)
    await db.commit()
    await db.refresh(db_audio_file)
    return db_audio_file

async def get_audio_files_by_owner(db: AsyncSession, owner_id: int):
    result = await db.execute(select(AudioFile).filter(AudioFile.owner_id == owner_id))
    return result.scalars().all()

async def delete_audio_file(db: AsyncSession, audio_file_id: int, owner_id: int):
    result = await db.execute(
        select(AudioFile).filter(AudioFile.id == audio_file_id, AudioFile.owner_id == owner_id)
    )
    db_audio_file = result.scalar_one_or_none()
    if db_audio_file:
        await db.delete(db_audio_file)
        await db.commit()
        return True
    return False

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = pwd_context.hash(user.password if user.password else "password")
    db_user = User(username=user.username, yandex_id=uuid4().hex, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user_id: int, new_username: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user:
        db_user.username = new_username
        await db.commit()
        await db.refresh(db_user)
        return db_user
    return None


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user:
        await db.delete(db_user)
        await db.commit()
        return True
    return False

async def get_user_by_yandex_id(db: AsyncSession, yandex_id: str):
    result = await db.execute(select(User).filter(User.yandex_id == yandex_id))
    return result.scalar_one_or_none()
