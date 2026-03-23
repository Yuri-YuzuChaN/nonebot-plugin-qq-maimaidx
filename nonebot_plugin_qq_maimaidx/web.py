import nonebot
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .libraries.image.update_table import *
from .libraries.service import mai

app: FastAPI = nonebot.get_app()

@app.get("/maimai/update")
async def _():
    await mai.update()
    await update_rating_table()
    await update_plate_table()
    return JSONResponse({"content": "Update Success"}, 200)