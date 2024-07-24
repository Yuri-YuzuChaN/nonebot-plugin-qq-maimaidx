from textwrap import dedent
from typing import Union

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
)
from nonebot.params import CommandArg, Depends
from PIL import Image

from ..libraries.maimaidx_best_50 import generate
from ..libraries.maimaidx_database import get_user
from ..libraries.maimaidx_error import UserNotBindError
from ..libraries.maimaidx_music import mai
from ..libraries.maimaidx_music_info import music_play_data
from ..libraries.maimaidx_player_score import music_global_data
from ..message import MessageSegment

best50 = on_command('b50', priority=5)
minfo = on_command('minfo', priority=5)
ginfo = on_command('ginfo', priority=5)


def get_qqid(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent, DirectMessageCreateEvent]) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id
    

@best50.handle()
async def _(event: Union[AtMessageCreateEvent, GroupAtMessageCreateEvent], arg: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        username = arg.extract_plain_text().strip()
        if isinstance(event, GroupAtMessageCreateEvent) and not username:
            user_id = get_user(user_id).QQID
        icon = event.author.avatar if isinstance(event, AtMessageCreateEvent) and not username else None
        pic = await generate(user_id, username, icon)
        if isinstance(pic, Image.Image):
            await best50.send(await MessageSegment.image(event, pic))
        else:
            await best50.send(pic)
    except UserNotBindError as e:
        await best50.send(str(e))


@minfo.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], arg: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        args = arg.extract_plain_text().strip()
        if not args:
            await minfo.finish('请输入曲目id或曲名')

        if mai.total_list.by_id(args):
            songs = args
        elif by_t := mai.total_list.by_title(args):
            songs = by_t.id
        else:
            aliases = mai.total_alias_list.by_alias(args)
            if not aliases:
                await minfo.finish('未找到曲目')
            elif len(aliases) != 1:
                msg = '找到相同别名的曲目，请使用以下ID查询：\n'
                for songs in aliases:
                    msg += f'{songs.SongID}：{songs.Name}\n'
                await minfo.finish(msg.strip())
            else:
                songs = str(aliases[0].SongID)
        pic = await music_play_data(user_id, songs)
        if isinstance(pic, Image.Image):
            pic = await MessageSegment.image(event, pic)
        await minfo.send(pic)
    except UserNotBindError as e:
        await minfo.send(str(e))


@ginfo.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if not args:
        await ginfo.finish('请输入曲目id或曲名')
    if args[0] not in '绿黄红紫白':
        level_index = 3
    else:
        level_index = '绿黄红紫白'.index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish('请输入曲目id或曲名')
    if mai.total_list.by_id(args):
        id = args
    elif by_t := mai.total_list.by_title(args):
        id = by_t.id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            await ginfo.finish('未找到曲目')
        elif len(alias) != 1:
            msg = '找到相同别名的曲目，请使用以下ID查询：\n'
            for songs in alias:
                msg += f'{songs.SongID}：{songs.Name}\n'
            await ginfo.finish(msg.strip())
        else:
            id = str(alias[0].SongID)
    music = mai.total_list.by_id(id)
    if not music.stats:
        await ginfo.finish('该乐曲还没有统计信息')
    if len(music.ds) == 4 and level_index == 4:
        await ginfo.finish('该乐曲没有这个等级')
    if not music.stats[level_index]:
        await ginfo.finish('该等级没有统计信息')
    stats = music.stats[level_index]
    pic = await MessageSegment.image(event, await music_global_data(music, level_index))
    data = pic + dedent(f'''\
        游玩次数：{round(stats.cnt)}
        拟合难度：{stats.fit_diff:.2f}
        平均达成率：{stats.avg:.2f}%
        平均 DX 分数：{stats.avg_dx:.1f}
        谱面成绩标准差：{stats.std_dev:.2f}
        ''')
    await ginfo.send(data)