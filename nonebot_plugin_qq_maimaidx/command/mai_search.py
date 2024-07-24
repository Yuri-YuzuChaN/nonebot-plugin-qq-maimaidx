import re
from typing import Union

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
)
from nonebot.params import CommandArg, Depends

from ..config import SONGS_PER_PAGE, diffs
from ..libraries.image import text_to_image
from ..libraries.maimaidx_database import get_user
from ..libraries.maimaidx_error import UserNotBindError
from ..libraries.maimaidx_model import Alias
from ..libraries.maimaidx_music import mai, maiApi
from ..libraries.maimaidx_music_info import draw_music_info
from ..message import MessageSegment

search = on_command('查歌', priority=5)
search_base = on_command('定数查歌', priority=5)
search_bpm = on_command('bpm查歌', priority=5)
search_artist = on_command('曲师查歌', priority=5)
search_charter = on_command('谱师查歌', priority=5)
search_alias_song = on_command('别名查歌', priority=5)
query_chart = on_command('id', priority=5)


def get_qqid(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent, DirectMessageCreateEvent]) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id


def song_level(ds1: float, ds2: float, stats1: str = None, stats2: str = None) -> list:
    result = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    if stats1:
        if stats2:
            stats1 = stats1 + ' ' + stats2
            stats1 = stats1.title()
        for music in sorted(music_data, key=lambda x: int(x.id)):
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    else:
        for music in sorted(music_data, key=lambda x: int(x.id)):
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    return result


@search.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], args: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    name = args.extract_plain_text().strip()
    if not name:
        return
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search.send('没有找到这样的乐曲。\n※ 如果是别名请使用「别名查歌」指令进行查询哦。')
    elif len(result) == 1:
        msg = await MessageSegment.image(event, await draw_music_info(result.random(), user_id))
        await search.send(msg)
    elif len(result) < 50:
        search_result = ''
        result.sort(key=lambda i: int(i.id))
        for music in result:
            search_result += f'{music.id}. {music.title}\n'
        await search.send(await MessageSegment.image(event, text_to_image(search_result)))
    else:
        await search.send(f'结果过多（{len(result)} 条），请缩小查询范围。')


@search_base.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], args: Message = CommandArg()):
    args = args.extract_plain_text().strip().split()
    if len(args) > 4 or len(args) == 0:
        await search_base.finish('命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>')
    if len(args) == 1:
        result = song_level(float(args[0]), float(args[0]))
    elif len(args) == 2:
        try:
            result = song_level(float(args[0]), float(args[1]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]))
    elif len(args) == 3:
        try:
            result = song_level(float(args[0]), float(args[1]), str(args[2]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]), str(args[2]))
    else:
        result = song_level(float(args[0]), float(args[1]), str(args[2]), str(args[3]))
    if not result:
        await search_base.finish('没有找到这样的乐曲。')
    if len(result) >= 60:
        await search_base.finish(f'结果过多（{len(result)} 条），请缩小搜索范围')
    msg = ''
    for i in result:
        msg += f'{i[0]}. {i[1]} {i[3]} {i[4]}({i[2]})\n'
    await search_base.send(await MessageSegment.image(event, text_to_image(msg)))


@search_bpm.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], args: Message = CommandArg()):
    args = args.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        music_data = mai.total_list.filter(bpm=int(args[0]))
    elif len(args) == 2:
        if (bpm := int(args[0])) > int(args[1]):
            page = int(args[1])
            music_data = mai.total_list.filter(bpm=bpm)
        else:
            music_data = mai.total_list.filter(bpm=(bpm, int(args[1])))
    elif len(args) == 3:
        music_data = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
        page = int(args[2])
    else:
        await search_bpm.finish('命令格式为：\nbpm查歌 <bpm>\nbpm查歌 <bpm下限> <bpm上限> (<页数>)')
    if not music_data:
        await search_bpm.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    music_data.sort(key=lambda x: int(x.basic_info.bpm))
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} bpm {m.basic_info.bpm}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_bpm.send(await MessageSegment.image(event, text_to_image(msg)))


@search_artist.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)')
    else:
        name = ''
        await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)')
    if not name:
        return
    music_data = mai.total_list.filter(artist_search=name)
    if not music_data:
        await search_artist.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} {m.basic_info.artist}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_artist.send(await MessageSegment.image(event, text_to_image(msg)))


@search_charter.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)')
    else:
        name = ''
        await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)')
    if not name:
        return
    music_data = mai.total_list.filter(charter_search=name)
    if not music_data:
        await search_charter.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            msg += f'No.{i + 1} {m.id}. {m.title} {" ".join([f"{d}/{c}" for d, c in diff_charter])}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_charter.send(await MessageSegment.image(event, text_to_image(msg)))


@search_alias_song.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    name = message.extract_plain_text().strip().lower()
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        obj = await maiApi.get_songs(name)
        if obj:
            if 'status' in obj and obj['status']:
                msg = f'未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n'
                for _s in obj['status']:
                    msg += f'- {_s["Tag"]}\n    ID {_s["SongID"]}: {name}\n'
                msg += f'※ 可以使用指令「同意别名 {_s["Tag"]}」进行投票'
                await search_alias_song.finish(msg.strip(), reply_message=True)
            else:
                alias_data = [Alias(**_a) for _a in obj]
    if alias_data:
        if len(alias_data) != 1:
            msg = f'找到{len(alias_data)}个相同别名的曲目：\n'
            for songs in alias_data:
                msg += f'{songs.SongID}：{songs.Name}\n'
            msg += '※ 请使用「id xxxxx」查询指定曲目'
            await search_alias_song.finish(msg.strip(), reply_message=True)
        else:
            music = mai.total_list.by_id(str(alias_data[0].SongID))
            await search_alias_song.finish('您要找的是不是：' + await MessageSegment.image(event, await draw_music_info(music, user_id)), reply_message=True)
    # id
    if name.isdigit() and (music := mai.total_list.by_id(name)):
        await search_alias_song.finish('您要找的是不是：' + await MessageSegment.image(event, await draw_music_info(music, user_id)), reply_message=True)
    if search_id := re.search(r'^id([0-9]*)$', name, re.IGNORECASE):
        music = music = mai.total_list.by_id(search_id.group(1))
        await search_alias_song.finish('您要找的是不是：' + await MessageSegment.image(event, await draw_music_info(music, user_id)), reply_message=True)
    # 标题
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_alias_song.finish(f'未找到别名为「{name}」的歌曲\n※ 可以使用「添加别名」指令给该乐曲添加别名\n※ 如果是歌名的一部分，请使用「查歌」指令查询哦。', reply_message=True)
    elif len(result) == 1:
        msg = await MessageSegment.image(event, await draw_music_info(result[0], user_id))
        await search_alias_song.finish('您要找的是不是：' + msg, reply_message=True)
    elif len(result) < 50:
        msg = f'未找到别名为「{name}」的歌曲，但找到{len(result)}个相似标题的曲目：\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            msg += f'{music.id}. {music.title}\n'
        msg += '※ 请使用「id xxxxx」查询指定曲目'
        await search_alias_song.finish(msg.strip(), reply_message=True)
    else:
        await search_alias_song.finish(f'结果过多（{len(result)} 条），请缩小查询范围。', reply_message=True)


@query_chart.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], args: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    id = args.extract_plain_text().strip()
    music = mai.total_list.by_id(id)
    if not music:
        msg = f'未找到ID为[{id}]的乐曲'
    else:
        msg = await MessageSegment.image(event, await draw_music_info(music, user_id))
    await query_chart.send(msg)