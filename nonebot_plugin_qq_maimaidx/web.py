import nonebot
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .config import Root, TempPicturePath, static
from .libraries.maimaidx_music import mai
from .libraries.maimaidx_update_table import *

app: FastAPI = nonebot.get_app()


@app.get('/maimai/{path}/{filename}')
async def _(path: str, filename: str):
    if path == 'rating':
        _p = static / 'mai' / 'rating'
    elif path == 'temp':
        _p = TempPicturePath
    elif path == 'help':
        _p = Root
    elif path == 'cover':
        _p = coverdir
    else:
        return JSONResponse({'error': 'File not found'}, 404)
    if (_p / filename).exists():
        return FileResponse(_p / filename)
    else:
        return JSONResponse({'error': 'File not found'}, 404)


@app.get('/maimai/update')
async def _():
    await mai.get_music()
    await mai.get_music_alias()
    await update_rating_table()
    return JSONResponse({'content': 'Update Success'}, 200)


@app.get('/maimai/updateplate')
async def _():
    await update_plate_table()
    return JSONResponse({'content': 'Update Success'}, 200)