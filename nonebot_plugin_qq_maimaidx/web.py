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
    await mai.get_plate_json()
    await update_rating_table()
    await update_plate_table()
    return JSONResponse({'content': 'Update Success'}, 200)