from pydantic import BaseModel


class APIResult(BaseModel):
    
    code: int = 0
    content: dict | list | str


class Alias(BaseModel):
    
    SongID: int
    Name: str
    Alias: list[str]