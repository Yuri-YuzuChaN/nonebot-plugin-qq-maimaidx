import re
from typing import List, Tuple, Union

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
    MessageSegment,
)
from nonebot.params import CommandArg, Depends

from ..config import SONGS_PER_PAGE, diffs
from ..libraries.image import image_to_bytesio, text_to_bytes_io, text_to_image
from ..libraries.maimaidx_database import get_user
from ..libraries.maimaidx_error import AliasesNotFoundError, UserNotBindError
from ..libraries.maimaidx_model import AliasStatus
from ..libraries.maimaidx_music import mai, maiApi
from ..libraries.maimaidx_music_info import draw_music_info

search_music              = on_command('查歌')
search_base         = on_command('定数查歌')
search_bpm          = on_command('bpm查歌')
search_artist       = on_command('曲师查歌')
search_charter      = on_command('谱师查歌')
search_alias_song   = on_command('别名查歌')
query_chart         = on_command('id')


def get_qqid(
    event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent, DirectMessageCreateEvent]
) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id


def song_level(ds1: float, ds2: float) -> List[Tuple[str, str, float, str]]:
    """
    查询定数范围内的乐曲
    
    Params:
        `ds1`: 定数下限
        `ds2`: 定数上限
    Return:
        `result`: 查询结果
    """
    result: List[Tuple[str, str, float, str]] = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    for music in sorted(music_data, key=lambda x: int(x.id)):
        if int(music.id) >= 100000:
            continue
        for i in music.diff:
            result.append((music.id, music.title, music.ds[i], diffs[i]))
    return result


@search_music.handle()
async def _(
    event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], 
    message: Message = CommandArg(), 
    user_id: str = Depends(get_qqid)
):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    name = message.extract_plain_text().strip()
    page = 1
    if not name:
        await search_music.finish('请输入关键词')
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_music.finish('没有找到这样的乐曲。\n※ 如果是别名请使用「别名查歌」指令进行查询哦。')
    if len(result) == 1:
        await search_music.finish(await draw_music_info(result.random(), user_id))
    
    search_result = ''
    result.sort(key=lambda i: int(i.id))
    for i, music in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{music.id}」":<7} {music.title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_music.send(MessageSegment.file_image(text_to_bytes_io(search_result)))


@search_base.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) > 4 or len(args) == 0:
        await search_base.finish('命令格式：\n定数查歌 「定数」\n定数查歌 「定数下限」 「定数上限」')
    page = 1
    if len(args) == 1:
        result = song_level(float(args[0]), float(args[0]))
    elif len(args) == 2:
        try:
            result = song_level(float(args[0]), float(args[1]))
        except:
            page = int(args[1]) if args[1].isdigit() else 1
            result = song_level(float(args[0]), float(args[0]))
    elif len(args) == 3:
        try:
            page = int(args[2]) if args[2].isdigit() else 1
            result = song_level(float(args[0]), float(args[1]))
        except:
            page = int(args[2]) if args[2].isdigit() else 1
            result = song_level(float(args[0]), float(args[0]))
    else:
        result = song_level(float(args[0]), float(args[1]))
        page = int(args[2]) if args[2].isdigit() else 1
    if not result:
        await search_base.finish('没有找到这样的乐曲。')
    
    search_result = ''
    for i, _result in enumerate(result):
        id, title, ds, diff = _result
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{id}」":<7}{f"「{diff}」":<11}{f"「{ds}」"} {title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_base.send(MessageSegment.file_image(text_to_bytes_io(search_result)))


@search_bpm.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        result = mai.total_list.filter(bpm=int(args[0]))
    elif len(args) == 2:
        if (bpm := int(args[0])) > int(args[1]):
            page = int(args[1])
            result = mai.total_list.filter(bpm=bpm)
        else:
            result = mai.total_list.filter(bpm=(bpm, int(args[1])))
    elif len(args) == 3:
        result = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
        page = int(args[2])
    else:
        await search_bpm.finish('命令格式：\nbpm查歌 「bpm」\nbpm查歌 「bpm下限」「bpm上限」「页数」')
    if not result:
        await search_bpm.finish('没有找到这样的乐曲。')
    
    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    result.sort(key=lambda x: int(x.basic_info.bpm))
    
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「BPM {m.basic_info.bpm}」":<9} {m.title} \n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_bpm.send(MessageSegment.file_image(text_to_bytes_io(search_result)))


@search_artist.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish('命令格式：\n曲师查歌「曲师名称」「页数」')
    else:
        await search_artist.finish('命令格式：\n曲师查歌「曲师名称」「页数」')

    result = mai.total_list.filter(artist_search=name)
    if not result:
        await search_artist.finish('没有找到这样的乐曲。')
    
    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「{m.basic_info.artist}」"} - {m.title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_artist.send(MessageSegment.file_image(text_to_bytes_io(search_result)))


@search_charter.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_charter.finish('命令格式：\n谱师查歌「谱师名称」「页数」')
    else:
        await search_charter.finish('命令格式：\n谱师查歌「谱师名称」「页数」')
    
    result = mai.total_list.filter(charter_search=name)
    if not result:
        await search_charter.finish('没有找到这样的乐曲。')
    
    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            search_result += f'''{f"「{m.id}」":<7}{" ".join([f"{f'「{d}」':<9}{f'「{c}」'}" for d, c in diff_charter])} {m.title}\n'''
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_charter.send(MessageSegment.file_image(text_to_bytes_io(search_result)))


@search_alias_song.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    name = message.extract_plain_text().strip().lower()
    error_msg = f'未找到别名为「{name}」的歌曲'
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        try:
            obj = await maiApi.get_songs(name)
            if obj:
                if type(obj[0]) == AliasStatus:
                    await search_alias_song.finish(error_msg)
                else:
                    alias_data = obj
        except AliasesNotFoundError:
            pass
    if alias_data:
        if len(alias_data) != 1:
            msg = f'找到{len(alias_data)}个相同别名的曲目：\n'
            for songs in alias_data:
                msg += f'{songs.SongID}：{songs.Name}\n'
            msg += '※ 请使用「id xxxxx」查询指定曲目'
            await search_alias_song.finish(msg.strip())
        else:
            music = mai.total_list.by_id(str(alias_data[0].SongID))
            if music:
                msg = '您要找的是不是：' + await draw_music_info(music, user_id)
            else:
                msg = error_msg
            await search_alias_song.finish(msg)
    
    # id
    if name.isdigit() and (music := mai.total_list.by_id(name)):
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(music, user_id))
    if search_id := re.search(r'^id([0-9]*)$', name, re.IGNORECASE):
        music = mai.total_list.by_id(search_id.group(1))
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(music, user_id))
    
    # 标题
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_alias_song.finish(error_msg)
    elif len(result) == 1:
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(result.random(), user_id))
    elif len(result) < 50:
        msg = f'未找到别名为「{name}」的歌曲，但找到{len(result)}个相似标题的曲目：\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            msg += f'{f"「{music.id}」":<7} {music.title}\n'
        msg += '※ 请使用「id xxxxx」查询指定曲目'
        await search_alias_song.finish(msg.strip())
    else:
        await search_alias_song.finish(f'结果过多「{len(result)}」条，请缩小查询范围。')


@query_chart.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    id = message.extract_plain_text().strip()
    music = mai.total_list.by_id(id)
    if not music:
        msg = f'未找到ID「{id}」的乐曲'
    else:
        msg = await draw_music_info(music, user_id)
    await query_chart.finish(msg)