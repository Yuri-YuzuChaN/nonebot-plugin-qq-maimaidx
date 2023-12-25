import nonebot
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .config import Root, TempPicturePath, static

app: FastAPI = nonebot.get_app()


@app.get('/maimai/{path}/{filename}')
async def _(path: str, filename: str):
    if path == 'rating':
        _p = static / 'mai' / 'rating'
    elif path == 'temp':
        _p = TempPicturePath
    elif path == 'help':
        _p = Root
    else:
        return JSONResponse({'error': 'File not found'}, 404)
    if (_p / filename).exists():
        return FileResponse(_p / filename)
    else:
        return JSONResponse({'error': 'File not found'}, 404)