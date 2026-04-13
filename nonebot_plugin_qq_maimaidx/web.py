import nonebot
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .libraries.image.update_table import *
from .libraries.service import mai

app: FastAPI = nonebot.get_app()

@app.get("/maimai/update")
async def _():
    await mai.update()
    table = UpdateTable()
    await table.update_rating_table()
    await table.update_level_15_rating_table()
    await table.update_plate_table()
    await table.update_wu_plate_table()
    return JSONResponse({"content": "Update Success"}, 200)