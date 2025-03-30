from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    yandex_id: str

    class Config:
        orm_mode = True

class AudioFileCreate(BaseModel):
    title: str

class AudioFile(BaseModel):
    id: int
    title: str
    path: str
    owner_id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    yandex_id: str | None = None