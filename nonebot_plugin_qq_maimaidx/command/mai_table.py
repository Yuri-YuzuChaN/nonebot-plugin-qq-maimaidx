import re

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
)
from nonebot.params import CommandArg, Depends

from ..libraries.maimaidx_database import get_user
from ..libraries.maimaidx_music_info import *
from ..libraries.maimaidx_player_score import *
from ..message import MessageSegment

rating_table = on_command('定数表', priority=5)
rating_table_pf = on_command('完成表', priority=5)
plate_process = on_command('牌子进度', priority=5)
level_process = on_command('等级进度', priority=5)
level_achievement_list = on_command('分数列表', priority=5)


def get_qqid(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent, DirectMessageCreateEvent]) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id


@rating_table.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    if args in levelList[:5]:
        await rating_table.send('只支持查询lv6-15的定数表')
    elif args in levelList[5:]:
        if args in levelList[-3:]:
            img = ratingdir / '14.png'
        else:
            img = ratingdir / f'{args}.png'
        if img.stat().st_size > 5000000:
            _i = Image.open(img)
            img = _i.resize((int(_i.size[0] * 0.7), int(_i.size[1] * 0.7)))
        await rating_table.send(await MessageSegment.image(event, img))
    else:
        await rating_table.send('无法识别的定数')


@rating_table_pf.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], args: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        args: str = args.extract_plain_text().strip()
        rating = re.search(r'^([0-9]+\+?)(app|fcp|ap|fc)?', args, re.IGNORECASE)
        plate = re.search(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉熊華华爽煌舞霸星宙祭祝])([極极将舞神者]舞?)$', args)
        if rating:
            ra = rating.group(1)
            plan = rating.group(2)
            if args in levelList[:5]:
                await rating_table_pf.send('只支持查询lv6-15的完成表')
            elif ra in levelList[5:]:
                pic = await draw_rating_table(user_id, ra, True if plan and plan.lower() in combo_rank else False)
                if isinstance(pic, Image.Image):
                    pic = await MessageSegment.image(event, pic.resize((int(pic.size[0] * 0.8), int(pic.size[1] * 0.8))))
                await rating_table_pf.send(pic)
            else:
                await rating_table_pf.send('无法识别的表格')
        elif plate:
            ver = plate.group(1)
            plan = plate.group(2)
            if ver in platecn:
                ver = platecn[ver]
            if ver in ['舞', '霸']:
                await rating_table_pf.finish('暂不支持查询「舞」系和「霸者」的牌子')
            if f'{ver}{plan}' == '真将':
                await rating_table_pf.finish('真系没有真将哦')
            pic = await draw_plate_table(user_id, ver, plan)
            if isinstance(pic, Image.Image):
                pic = await MessageSegment.image(event, pic)
            await rating_table_pf.send(pic)
        else:
            await rating_table_pf.send('无法识别的表格')
    except UserNotBindError as e:
        await rating_table_pf.send(str(e))
        

@plate_process.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        username = None
        args = message.extract_plain_text().lower()
        match = re.search(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉熊華华爽舞霸星宙祭祝双])([極极将舞神者]舞?)$', args)
        if not match:
            await plate_process.finish('输入错误，请重新确定牌子')
        ver = match.group(1)
        plan = match.group(2)
        if f'{ver}{plan}' == '真将':
            await plate_process.finish('真系没有真将哦')

        data = await player_plate_data(user_id, username, ver, plan)
        if isinstance(data, Image.Image):
            data = await MessageSegment.image(event, data)
        await plate_process.send(data)
    except UserNotBindError as e:
        await plate_process.send(str(e))


@level_process.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        args = message.extract_plain_text().lower()
        match = re.search(r'([0-9]+\+?)\s?([abcdsfxp\+]+)\s?([\u4e00-\u9fa5]+)?\s?([0-9]+)?\s?(.+)?', args)
        if not match:
            await level_process.finish('输入错误，请重新输入难度等级')
        level = match.group(1)
        plan = match.group(2)
        category = match.group(3)
        page = match.group(4)
        username = match.group(5)
        
        if level not in levelList:
            await level_process.finish('无此等级')
        if plan.lower() not in scoreRank + comboRank + syncRank:
            await level_process.finish('无此评价等级')
        if levelList.index(level) < 11 or (plan.lower() in scoreRank and scoreRank.index(plan.lower()) < 8):
            await level_process.finish('兄啊，有点志向好不好')
        if category:
            if category in ['已完成', '未完成', '未开始']:
                _c = {
                    '已完成': 'completed',
                    '未完成': 'unfinished',
                    '未开始': 'notstarted',
                    '未游玩': 'notstarted'
                }
                category = _c[category]
            else:
                await level_process.finish(f'无法指定查询「{category}」')
        else:
            category = 'default'
        
        data = await level_process_data(user_id, username, level, plan, category, int(page) if page else 1)
        if isinstance(data, Image.Image):
            data = await MessageSegment.image(event, data)
        await level_process.send(data)
    except UserNotBindError as e:
        await level_process.send(str(e))


@level_achievement_list.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        args = message.extract_plain_text().lower()
        match = re.search(r'([0-9]+\.?[0-9]?\+?)\s?([0-9]+)?\s?(.+)?', args)
        if not match:
            await level_achievement_list.finish('输入错误，请重新输入指定等级')
        rating = match.group(1)
        page = match.group(2)
        username = match.group(3)
        try:
            if '.' in rating:
                rating = round(float(rating), 1)
            elif rating not in levelList:
                await level_achievement_list.finish('无此等级')
        except ValueError:
            if rating not in levelList:
                await level_achievement_list.finish('无此等级')

        data = await level_achievement_list_data(user_id, username, rating, int(page) if page else 1)
        if isinstance(data, Image.Image):
            data = await MessageSegment.image(event, data)
        await level_achievement_list.send(data)
    except UserNotBindError as e:
        await level_achievement_list.send(str(e))