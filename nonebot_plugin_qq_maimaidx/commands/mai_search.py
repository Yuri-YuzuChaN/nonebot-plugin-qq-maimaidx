import re

from nonebot import on_command
from nonebot.adapters.qq import Message, MessageSegment
from nonebot.exception import FinishedException
from nonebot.params import CommandArg, Depends

from ..core.clients.yuzuchan.client import YuzuChaNAPI
from ..core.clients.yuzuchan.models import StatusEnum
from ..core.database.qq import User
from ..core.handler import draw_chart_info, draw_song_list
from ..core.merge.alias import yuzu_alias_to_alias
from ..core.merge.models import Song
from ..core.service import mai
from .depend import GetUserAndAuthOrNone, process_regex

search = on_command("查歌")
search_alias_song = on_command("别名查歌")
query_chart = on_command("id")


@search.handle()
async def _(
    result: tuple[list[Song], int] = Depends(process_regex),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    songs, page = result
    if not songs:
        await search.finish(
            (
                "没有找到这样的乐曲。\n"
                "※ 指令：/查歌 「定数|bpm|曲师|谱师」「内容」\n"
                "※ 指令：/查歌 「标题内容」"
            )
        )

    if len(songs) == 1:
        image = await draw_chart_info(songs[0], user)
    elif len(songs) <= 5:
        r = ""
        for song in songs:
            r += f"{f'「{song.song_id}」':<7} {song.song_name}\n"
        image = MessageSegment.text(r)
    else:
        image = await draw_song_list(songs, page)
    await search.send(image)


@search_alias_song.handle()
async def _(
    message: Message = CommandArg(), user: User | None = Depends(GetUserAndAuthOrNone)
):
    args = message.extract_plain_text().strip().split()
    if len(args) == 0:
        await search_alias_song.finish("请输入要查询的别名")
    name = ""
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_alias_song.finish("参数错误，页码必须为数字")
    else:
        await search_alias_song.finish("参数错误，指令格式：/别名查歌 别名")

    error_msg = f"未找到别名为「{name}」的歌曲"
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        try:
            api = YuzuChaNAPI()
            obj = await api.get_songs(name)
            if obj.type == StatusEnum.ONGOING:
                msg = f"未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n"
                for _s in obj.data:
                    msg += f"- {_s.tag}\n    ID {_s.song_id}: {_s.name}\n"
                msg += "※ 可以使用指令「同意别名 XXXXX」进行投票"
                await search_alias_song.finish(msg.strip())
            else:
                alias_data = yuzu_alias_to_alias(obj.data)
        except FinishedException:
            raise
        except Exception:
            pass

    if alias_data:
        if len(alias_data) != 1:
            msg = f"找到{len(alias_data)}个相同别名的曲目：\n"
            for songs in alias_data:
                msg += f"{songs.song_id}：{songs.alias[0]}\n"
            msg += "※ 请使用「/id xxxxx」查询指定曲目"
            await search_alias_song.finish(msg.strip())
        else:
            song = mai.total_list.by_id(alias_data[0].song_id)
            if song:
                msg = "您要找的是不是：" + await draw_chart_info(song, user)
            else:
                msg = error_msg
            await search_alias_song.finish(msg)

    # id
    if name.isdigit() and (song := mai.total_list.by_id(int(name))):
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user)
        )
    if search_id := re.search(r"^id([0-9]*)$", name, re.IGNORECASE):
        song = mai.total_list.by_id(int(search_id.group(1)))
        if not song:
            await search_alias_song.finish(f"未找到ID「{search_id.group(1)}」的乐曲")
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user)
        )

    # 标题
    result = mai.total_list.filter(title=name)
    if len(result) == 0:
        msg = error_msg
    elif len(result) == 1:
        msg = "您要找的是不是：" + await draw_chart_info(result[0], user)
    elif len(result) < 5:
        msg_ = (
            f"未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n"
        )
        for song in sorted(result, key=lambda x: int(x.song_id)):
            msg_ += f"{f'「{song.song_id}」':<7} {song.song_name}\n"
        msg_ += "※ 请使用「/id xxxxx」查询指定曲目"
        msg = msg_
    else:
        msg = (
            f"未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n"
        )
        msg += await draw_song_list(result, page)
    await search_alias_song.finish(msg)


@query_chart.handle()
async def _(
    message: Message = CommandArg(), user: User = Depends(GetUserAndAuthOrNone)
):

    _id = message.extract_plain_text().strip()
    if not _id.isdigit():
        await query_chart.finish("请输入正确的曲目ID")

    song = mai.total_list.by_id(int(_id))
    if not song:
        msg = f"未找到ID「{_id}」的乐曲"
    else:
        msg = await draw_chart_info(song, user)
    await query_chart.finish(msg)
