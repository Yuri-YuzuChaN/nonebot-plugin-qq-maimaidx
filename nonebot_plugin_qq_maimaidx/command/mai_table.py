import re

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
)
from nonebot.params import CommandArg, Depends

from ..constants import *
from ..libraries.clients.exceptions import UserNotBindError
from ..libraries.database.qq_database import get_user
from ..libraries.search import draw_rating_table_text
from ..libraries.search_df import *

rating_table            = on_command("定数表")
rating_table_pf         = on_command("完成表")
plate_process           = on_command("牌子进度")
level_process           = on_command("等级进度")
level_achievement_list  = on_command("分数列表")


TABLE_PATTERN = (
    r"^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜彩])"
    r"([極极将舞神者]舞?)$"
)
RATING_PATTERN = r"^([0-9]+\+?)(ap|app|fc|fcp|fs|fsp|fdx|fdxp)?"
LEVEL_PATTERN = r"([0-9]+\+?)\s?([abcdsfxp\+]+)\s?([\u4e00-\u9fa5]+)?\s?([0-9]+)?\s?(.+)?"
LEVEL_LIST_PATTERN = r"([0-9]+\.?[0-9]?\+?)\s?([0-9]+)?\s?(.+)?"


def get_qqid(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent | DirectMessageCreateEvent
) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id


@rating_table.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg()
):
    rating = message.extract_plain_text().strip()
    if rating in LEVEL_LIST[:6]:
        await rating_table.send("只支持查询lv7-15的定数表")
    elif rating in LEVEL_LIST[6:]:
        pic = draw_rating_table_text(rating)
        await rating_table.send(pic)
    else:
        await rating_table.send("无法识别的定数")


@rating_table_pf.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user_id: str = Depends(get_qqid)
):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = (await get_user(user_id)).QQID
        
        args = message.extract_plain_text().strip()
        _rating = re.search(RATING_PATTERN, args, re.IGNORECASE)
        plate = re.search(TABLE_PATTERN, args)
        
        if _rating:
            rating = _rating.group(1)
            plan = _rating.group(2)
            if args in LEVEL_LIST[:6]:
                result = "只支持查询lv7-15的完成表"
            elif rating in LEVEL_LIST[6:]:
                _p = True if plan and plan.lower() in COMBO_SP + SYNC_SP else False
                result = await draw_df_rating_table(user_id, rating, _p)
            else:
                result = "无法识别的表格"
        elif plate:
            version = plate.group(1)
            plan = plate.group(2)
            if version in PLATE_CN:
                version = PLATE_CN[version]
            if f"{version}{plan}" == "真将":
                await rating_table_pf.finish("真代没有真将哦")
            result = await draw_df_plate_table(user_id, version, plan)
        else:
            result = "无法识别的表格"
    except UserNotBindError as e:
        result = str(e)
    
    await rating_table_pf.send(result)
        

@plate_process.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user_id: str = Depends(get_qqid)
):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = (await get_user(user_id)).QQID
        username = None
        args = message.extract_plain_text().lower()
        match = re.search(TABLE_PATTERN, args)
        if not match:
            await plate_process.finish("输入错误，请重新确定牌子")
        ver = match.group(1)
        plan = match.group(2)
        if f"{ver}{plan}" == "真将":
            await plate_process.finish("真系没有真将哦")

        data = await draw_df_plate_process(user_id, username, ver, plan)
        await plate_process.send(data)
    except UserNotBindError as e:
        await plate_process.send(str(e))


@level_process.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user_id: str = Depends(get_qqid)
):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = (await get_user(user_id)).QQID
        args = message.extract_plain_text().lower()
        match = re.search(LEVEL_PATTERN, args)
        if not match:
            await level_process.finish("输入错误，请重新输入难度等级")
        level = match.group(1)
        plan = match.group(2)
        CATEGORY = match.group(3)
        page = match.group(4)
        username = match.group(5)
        
        if level not in LEVEL_LIST:
            await level_process.finish("无此等级")
        if plan.lower() not in RANK_PLUS + COMBO_PLUS + SYNC_PLUS:
            await level_process.finish("无此评价等级")
        if LEVEL_LIST.index(level) < 11 or (
            plan.lower() in RANK_PLUS and RANK_PLUS.index(plan.lower()) < 8
        ):
            await level_process.finish("兄啊，有点志向好不好")
        if CATEGORY:
            if CATEGORY in ["已完成", "未完成", "未开始"]:
                _c = {
                    "已完成": "completed",
                    "未完成": "unfinished",
                    "未开始": "notstarted",
                    "未游玩": "notstarted"
                }
                CATEGORY = _c[CATEGORY]
            else:
                await level_process.finish(f"无法指定查询「{CATEGORY}」")
        else:
            CATEGORY = "default"
        
        data = await draw_df_level_process(
            user_id, 
            username, 
            level, 
            plan, 
            CATEGORY, 
            int(page) if page else 1
        )
        await level_process.send(data)
    except UserNotBindError as e:
        await level_process.send(str(e))


@level_achievement_list.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user_id: str = Depends(get_qqid)
):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = (await get_user(user_id)).QQID
        args = message.extract_plain_text().lower()
        match = re.search(LEVEL_LIST_PATTERN, args)
        if not match:
            await level_achievement_list.finish("输入错误，请重新输入指定等级")
        rating = match.group(1)
        page = match.group(2)
        username = match.group(3)
        try:
            if "." in rating:
                rating = round(float(rating), 1)
            elif rating not in LEVEL_LIST:
                await level_achievement_list.finish("无此等级")
        except ValueError:
            if rating not in LEVEL_LIST:
                await level_achievement_list.finish("无此等级")

        data = await draw_df_level_achievement_list(
            user_id, 
            username, 
            rating, 
            int(page) if page else 1
        )
        await level_achievement_list.finish(data)
    except UserNotBindError as e:
        await level_achievement_list.send(str(e))