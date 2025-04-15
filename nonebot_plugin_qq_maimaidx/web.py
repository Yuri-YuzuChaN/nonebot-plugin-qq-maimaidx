import nonebot
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .libraries.maimaidx_music import mai
from .libraries.maimaidx_update_table import *

app: FastAPI = nonebot.get_app()

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