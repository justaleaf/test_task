from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AudioFile
import os

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