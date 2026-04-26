import re

from nonebot import on_command
from nonebot.adapters.qq import Message
from nonebot.params import CommandArg, Depends

from ..constants import *
from ..core.database.qq import User
from ..core.merge.models.category import Category
from ..core.search import (
    draw_level_progress,
    draw_level_score_list,
    draw_plate_progress,
    draw_plate_table,
    draw_rating_table,
    draw_rating_table_text,
)
from .extra import get_user_db

TABLE_PATTERN = (
    r"^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜彩])"
    r"([極极将舞神者]舞?)\s?([12])?"
)
RATING_PATTERN = r"^([0-9]+\+?)(ap|app|fc|fcp|fs|fsp|fdx|fdxp)?"
LEVEL_PATTERN = r"([0-9]+\+?)\s?([abcdsfxp\+]+)\s?([\u4e00-\u9fa5]+)?\s?([0-9]+)?\s?(.+)?"
LEVEL_LIST_PATTERN = r"([0-9]+\.?[0-9]?\+?)\s?([0-9]+)?\s?(.+)?"
CATEGORY_ALIAS = {
    "已完成": Category.COMPLETED,
    "未完成": Category.UNFINISHED,
    "未开始": Category.NOTPLAYED,
    "未游玩": Category.NOTPLAYED,
}


rating_table            = on_command("定数表")
rating_table_pf         = on_command("完成表")
plate_process           = on_command("牌子进度")
level_process           = on_command("等级进度")
level_score_list        = on_command("分数列表")



@rating_table.handle()
async def _(message: Message = CommandArg()):
    rating = message.extract_plain_text().strip()
    if rating in LEVEL_LIST[:6]:
        result = "只支持查询lv7-15的定数表"
    elif rating in LEVEL_LIST[6:]:
        result = draw_rating_table_text(rating)
    else:
        result = "无法识别的定数"
    await rating_table.send(result)


@rating_table_pf.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    args = message.extract_plain_text().strip()
    _rating = re.search(RATING_PATTERN, args, re.IGNORECASE)
    plate = re.search(TABLE_PATTERN, args)
    
    if _rating:
        rating = _rating.group(1)
        plan = _rating.group(2)
        if args in LEVEL_LIST[:6]:
            result = "只支持查询lv7-15的完成表"
        elif rating in LEVEL_LIST[6:]:
            plan_ = True if plan and plan.lower() in COMBO_SP + SYNC_SP else False
            result = await draw_rating_table(user, rating, plan_)
        else:
            result = "无法识别的表格"
    elif plate:
        version = plate.group(1)
        plan = plate.group(2)
        page = plate.group(3) or 1
        if f"{version}{plan}" == "真将":
            await rating_table_pf.finish("真代没有真将哦")
        result = await draw_plate_table(user, version, plan, int(page))
    else:
        result = "无法识别的表格"
    
    await rating_table_pf.send(result)
        

@plate_process.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    username = None
    args = message.extract_plain_text().lower()
    match = re.search(TABLE_PATTERN, args)
    if not match:
        await plate_process.finish("输入错误，请重新确定牌子")
    ver = match.group(1)
    plan = match.group(2)
    if f"{ver}{plan}" == "真将":
        await plate_process.finish("真系没有真将哦")

    data = await draw_plate_progress(user, username, ver, plan)
    await plate_process.send(data)


@level_process.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    args = message.extract_plain_text().lower()
    match = re.search(LEVEL_PATTERN, args)
    if not match:
        await level_process.finish("输入错误，请重新输入难度等级")
    level = match.group(1)
    plan = match.group(2)
    category_ = match.group(3)
    page = match.group(4) or 1
    username = match.group(5)
    
    if level not in LEVEL_LIST:
        await level_process.finish("无此等级")
    if plan.lower() not in RANK_PLUS + COMBO_PLUS + SYNC_PLUS:
        await level_process.finish("无此评价等级")
    if LEVEL_LIST.index(level) < 11 or (
        plan.lower() in RANK_PLUS and RANK_PLUS.index(plan.lower()) < 8
    ):
        await level_process.finish("兄啊，有点志向好不好")
    if category_:
        target_category = CATEGORY_ALIAS.get(category_)
        if target_category:
            category = target_category
        else:
            await level_process.finish(f"无法指定查询「{category_}」")
    else:
        category = Category.DEFAULT
    
    data = await draw_level_progress(
        user, 
        level, 
        plan, 
        category, 
        int(page)
    )
    await level_process.send(data)


@level_score_list.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    args = message.extract_plain_text().lower()
    match = re.search(LEVEL_LIST_PATTERN, args)
    if not match:
        await level_score_list.finish("输入错误，请重新输入指定等级")
    rating = match.group(1)
    page = match.group(2) or 1
    username = match.group(3)
    try:
        if "." in rating:
            rating = round(float(rating), 1)
        elif rating not in LEVEL_LIST:
            await level_score_list.finish("无此等级")
    except ValueError:
        if rating not in LEVEL_LIST:
            await level_score_list.finish("无此等级")

    result = await draw_level_score_list(user, rating, int(page), username)
    await level_score_list.finish(result)