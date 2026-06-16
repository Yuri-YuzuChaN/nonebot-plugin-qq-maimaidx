import re

from nonebot import on_command
from nonebot.adapters.qq import Message, MessageSegment
from nonebot.params import CommandArg, Depends

from ..constants import COMBO_PLUS, LEVEL_LIST, RANK_PLUS, SYNC_PLUS
from ..core.database.qq import User
from ..core.handler import (
    draw_level_progress,
    draw_level_score_list,
    draw_plate_progress,
    draw_plate_table,
    draw_rating_table,
    draw_rating_table_text,
)
from ..core.merge.models import Category
from ..resources import pic_dir
from .depend import GetUserAndAuth

RATING_PATTERN = r"^([0-9]+\+?)((s+|ap|fc|fs|fdx)\+?)?\s?"
TABLE_PATTERN = (
    r"^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜彩])"
    r"([極极将舞神者]舞?)\s?([12]+)?$"
)
LEVEL_PATTERN = r"^([0-9]+\+?)\s?((a+|b+|c|d|s+|ap|fc|fs|fdx)\+?)\s?([\u4e00-\u9fa5]+)?\s?([0-9]+)?$"
LEVEL_LIST_PATTERN = r"^([0-9]+(?:\.[0-9]+)?\+?)\s?([0-9]+)?$"
CATEGORY_ALIAS = {
    "已完成": Category.COMPLETED,
    "未完成": Category.UNFINISHED,
    "未开始": Category.NOTPLAYED,
    "未游玩": Category.NOTPLAYED,
}


rating_table = on_command("定数表")
rating_table_pfm = on_command("完成表")
plate_table_condition = on_command("牌子条件")
plate_progress = on_command("牌子进度")
level_progress = on_command("等级进度")
level_score_list = on_command("分数列表")


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


@rating_table_pfm.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetUserAndAuth)):
    args = message.extract_plain_text().strip()
    _rating = re.search(RATING_PATTERN, args, re.IGNORECASE)
    plate = re.search(TABLE_PATTERN, args)

    if _rating:
        ra = _rating.group(1)
        plan = _rating.group(2)
        if args in LEVEL_LIST[:6]:
            result = "只支持查询lv7-15的完成表"
        elif ra in LEVEL_LIST[6:]:
            if plan and plan.lower() not in COMBO_PLUS:
                await rating_table_pfm.finish(
                    "完成表目前仅支持「fc」「ap」计划，例如「13fc完成表」「13ap完成表」。",
                )
            result = await draw_rating_table(
                user, ra, True if plan and plan.lower() in COMBO_PLUS else False
            )
        else:
            result = "无法识别的表格"
    elif plate:
        version = plate.group(1)
        plan = plate.group(2)
        page = plate.group(3) or 1
        if f"{version}{plan}" == "真将":
            await rating_table_pfm.finish("真代没有真将哦")
        result = await draw_plate_table(user, version, plan, int(page))
    else:
        result = "无法识别的表格"

    await rating_table_pfm.send(result)


@plate_table_condition.handle()
async def _():
    await plate_table_condition.send(
        MessageSegment.file_image(pic_dir / "table_condition.jpg")
    )


@plate_progress.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetUserAndAuth)):
    args = message.extract_plain_text().lower()
    match = re.search(TABLE_PATTERN, args)
    if not match:
        await plate_progress.finish("输入错误，请重新确定牌子")
    ver = match.group(1)
    plan = match.group(2)
    page = match.group(3) or 1
    if f"{ver}{plan}" == "真将":
        await plate_progress.finish("真系没有真将哦")

    data = await draw_plate_progress(user, ver, plan, int(page))
    await plate_progress.send(data)


@level_progress.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetUserAndAuth)):
    args = message.extract_plain_text().lower()
    match = re.search(LEVEL_PATTERN, args)
    if not match:
        await level_progress.finish("输入错误，请重新输入难度等级")
    level = match.group(1)
    plan = match.group(2).lower()
    category_ = match.group(3)
    page = match.group(4) or 1

    if level not in LEVEL_LIST:
        await level_progress.finish("无此等级")
    if plan.lower() not in RANK_PLUS + COMBO_PLUS + SYNC_PLUS:
        await level_progress.finish("无此评价等级")
    if LEVEL_LIST.index(level) < 11 or (
        plan.lower() in RANK_PLUS and RANK_PLUS.index(plan.lower()) < 8
    ):
        await level_progress.finish("兄啊，有点志向好不好")
    if category_:
        target_category = CATEGORY_ALIAS.get(category_)
        if target_category:
            category = target_category
        else:
            await level_progress.finish(f"无法指定查询「{category_}」。")
    else:
        category = Category.DEFAULT

    data = await draw_level_progress(user, level, plan, category, int(page))
    await level_progress.send(data)


@level_score_list.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetUserAndAuth)):
    args = message.extract_plain_text().lower()
    match = re.search(LEVEL_LIST_PATTERN, args)
    if not match:
        await level_score_list.finish("输入错误，请重新输入指定等级")
    rating = match.group(1)
    page = match.group(2) or 1
    if "." in rating:
        # 定数仅有一位小数，多位小数视为输入有误
        if not re.fullmatch(r"[0-9]+\.[0-9]", rating):
            await level_score_list.finish("输入有误，定数仅有一位小数。")
        rating = round(float(rating), 1)
    elif rating not in LEVEL_LIST:
        await level_score_list.finish("无此等级")

    result = await draw_level_score_list(user, rating, int(page))
    await level_score_list.finish(result)
