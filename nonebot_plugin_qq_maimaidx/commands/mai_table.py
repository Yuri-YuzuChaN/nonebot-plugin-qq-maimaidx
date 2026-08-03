import re
from re import Match

from nonebot.adapters.qq import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends, RegexMatched

from ..constants import COMBO_PLUS, LEVEL_LIST, PLATE_CN, RANK_PLUS, SYNC_PLUS
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
from .depend import GetUserAndAuth, UniCommand
from .router import on_command, on_regex

RATING_PATTERN = r"^([0-9]+\+?)((s+|ap|fc|fs|fdx)\+?)?\s?"
TABLE_PATTERN = (
    r"^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜彩])"
    r"([極极将舞神者]舞?){}表?\s?([0-9]+)?$"
)
LEVEL_PATTERN = r"^([0-9]+\+?)\s?((?:a+|b+|c|d|s+|ap|fc|fs|fdx)\+?)\s?([\u4e00-\u9fa5]+)?\s?{}\s?([0-9]+)?$"
LEVEL_LIST_PATTERN = r"^([0-9]+(?:\.[0-9]+)?\+?)\s?{}\s?([0-9]+)?$"

CATEGORY_ALIAS = {
    "已完成": Category.COMPLETED,
    "未完成": Category.UNFINISHED,
    "未开始": Category.NOTPLAYED,
    "未游玩": Category.NOTPLAYED,
}


# 定数表
rating_table = on_command("定数表")
rating_table_regex = on_regex(r"([0-9]+\+?)定数表$")


@rating_table.handle()
@rating_table_regex.handle()
async def _(
    matcher: Matcher,
    rating: str = Depends(UniCommand()),
):
    if rating in LEVEL_LIST[:6]:
        result = "只支持查询lv7-15的定数表"
    elif rating in LEVEL_LIST[6:]:
        result = draw_rating_table_text(rating)
    else:
        result = "无法识别的定数"
    await matcher.send(result, reply_message=True)


async def parse_plate_args(matcher: Matcher, match: Match[str]) -> tuple[str, str, int]:
    version = PLATE_CN.get(match.group(1), match.group(1))
    plan = match.group(2)
    page = int(match.group(3) or 1)
    if f"{version}{plan}" == "真将":
        await matcher.finish("真系没有真将哦", reply_message=True)
    return version, plan, page


# 完成表
rating_table_pfm = on_command("完成表")
rating_table_pfm_regex = on_regex(RATING_PATTERN + r"完成表$", re.IGNORECASE)


@rating_table_pfm.handle()
@rating_table_pfm_regex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=0)),
    user: User = Depends(GetUserAndAuth),
):
    _rating = re.search(RATING_PATTERN, args, re.IGNORECASE)
    plate = re.search(TABLE_PATTERN, args)

    if _rating:
        ra = _rating.group(1)
        plan = _rating.group(2)
        if ra in LEVEL_LIST[:6]:
            result = "只支持查询lv7-15的完成表"
        elif ra in LEVEL_LIST[6:]:
            if plan and plan.lower() not in COMBO_PLUS:
                await matcher.finish(
                    "完成表目前仅支持「fc」「ap」计划，例如「13fc完成表」「13ap完成表」。",
                    reply_message=True,
                )
            result = await draw_rating_table(
                user, ra, True if plan and plan.lower() in COMBO_PLUS else False
            )
        else:
            result = "无法识别的表格"
    elif plate:
        version, plan, page = await parse_plate_args(matcher, plate)
        result = await draw_plate_table(user, version, plan, page)
    else:
        result = "无法识别的表格"

    await matcher.send(result, reply_message=True)


# 牌子表格
plate_table_pfm = on_regex(TABLE_PATTERN.format("完成"))
plate_progress_rex = on_regex(TABLE_PATTERN.format("进度"))
plate_progress = on_command("牌子进度")


@plate_table_pfm.handle()
@plate_progress_rex.handle()
async def _(
    matcher: Matcher,
    match: Match[str] = RegexMatched(),
    user: User = Depends(GetUserAndAuth),
):
    version, plan, page = await parse_plate_args(matcher, match)
    if isinstance(matcher, plate_table_pfm):
        pic = await draw_plate_table(user, version, plan, page)
    else:
        pic = await draw_plate_progress(user, version, plan, page)
    await matcher.finish(pic, reply_message=True)


@plate_progress.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetUserAndAuth)):
    args = message.extract_plain_text().lower()
    match = re.search(TABLE_PATTERN, args)
    if not match:
        await plate_progress.finish("输入错误，请重新确定牌子", reply_message=True)
    version, plan, page = await parse_plate_args(plate_progress, match)
    result = await draw_plate_progress(user, version, plan, page)
    await plate_progress.send(result, reply_message=True)


# 等级进度
level_progress = on_command("等级进度")
level_progress_rex = on_regex(LEVEL_PATTERN.format("进度"), re.IGNORECASE)


@level_progress.handle()
@level_progress_rex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=0)),
    user: User = Depends(GetUserAndAuth),
):
    args = args.lower()
    match = re.search(LEVEL_PATTERN.format("进度"), args, re.IGNORECASE)
    if not match:
        match = re.search(LEVEL_PATTERN.format(""), args, re.IGNORECASE)
    if not match:
        await matcher.finish("输入错误，请重新输入难度等级", reply_message=True)
    level = match.group(1)
    plan = match.group(2).lower()
    category_ = match.group(3)
    page = int(match.group(4) or 1)

    if level not in LEVEL_LIST:
        await matcher.finish("无此等级", reply_message=True)
    if plan not in RANK_PLUS + COMBO_PLUS + SYNC_PLUS:
        await matcher.finish("无此评价等级", reply_message=True)
    if LEVEL_LIST.index(level) < 11 or (
        plan in RANK_PLUS and RANK_PLUS.index(plan) < 8
    ):
        await matcher.finish("兄啊，有点志向好不好", reply_message=True)
    if category_:
        target_category = CATEGORY_ALIAS.get(category_)
        if target_category:
            category = target_category
        else:
            await matcher.finish(f"无法指定查询「{category_}」。", reply_message=True)
    else:
        category = Category.DEFAULT

    data = await draw_level_progress(user, level, plan, category, page)
    await matcher.send(data, reply_message=True)


# 分数列表
level_score_list = on_command("分数列表")
level_score_list_rex = on_regex(LEVEL_LIST_PATTERN.format("分数列表"))


@level_score_list.handle()
@level_score_list_rex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=0)),
    user: User = Depends(GetUserAndAuth),
):
    args = args.lower()
    match = re.search(LEVEL_LIST_PATTERN.format("分数列表"), args)
    if not match:
        match = re.search(LEVEL_LIST_PATTERN.format(""), args)
    if not match:
        await matcher.finish("输入错误，请重新输入指定等级", reply_message=True)
    rating = match.group(1)
    page = int(match.group(2) or 1)
    if "." in rating:
        if not re.fullmatch(r"[0-9]+\.[0-9]", rating):
            await matcher.finish("输入有误，定数仅有一位小数。", reply_message=True)
        rating = round(float(rating), 1)
    elif rating not in LEVEL_LIST:
        await matcher.finish("无此等级", reply_message=True)

    result = await draw_level_score_list(user, rating, page)
    await matcher.finish(result, reply_message=True)


# 牌子条件
plate_table_condition = on_command("牌子条件")


@plate_table_condition.handle()
async def _():
    await plate_table_condition.send(
        MessageSegment.file_image(pic_dir / "table_condition.jpg"),
        reply_message=True,
    )
