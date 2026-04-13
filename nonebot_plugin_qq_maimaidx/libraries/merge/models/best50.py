from pydantic import BaseModel

from .score import PlayResult


class Best50(BaseModel):
    
    sd_total: int
    dx_total: int
    sd: list[PlayResult] = []
    dx: list[PlayResult] = []