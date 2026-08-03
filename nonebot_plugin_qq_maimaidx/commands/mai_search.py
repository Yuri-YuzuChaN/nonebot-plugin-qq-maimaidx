import re

from nonebot.adapters.qq import MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Depends

from ..core.clients.yuzuchan.client import YuzuChaNAPI
from ..core.clients.yuzuchan.models import AliasStatus, Songs, StatusEnum
from ..core.database.qq import User
from ..core.handler import draw_chart_info, draw_song_list
from ..core.merge.alias import yuzu_alias_to_alias
from ..core.merge.models import Song
from ..core.service import mai
from .depend import GetUserAndAuthOrNone, UniCommand, process_regex
from .router import on_command, on_regex

search = on_command("查歌")
search_regex = on_regex(r"^(定数|bpm|曲师|谱师)?查歌\s?(.+)", re.IGNORECASE)
search_alias_song = on_command("别名查歌")
search_alias_song_regex = on_regex(
    r"(.+)是(?:什么|啥)歌[？?]?([0-9]+)?$", re.IGNORECASE
)
query_chart = on_command("id")
query_chart_regex = on_regex(r"^id\s?([0-9]+)$", re.IGNORECASE)


@search.handle()
@search_regex.handle()
async def _(
    matcher: Matcher,
    result: tuple[list[Song], int] = Depends(process_regex),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    songs, page = result
    if not songs:
        await matcher.finish(
            (
                "没有找到这样的乐曲。\n"
                "※ 指令：/查歌 「定数|bpm|曲师|谱师」「内容」\n"
                "※ 指令：/查歌 「标题内容」"
            ),
            reply_message=True,
        )

    if len(songs) == 1:
        image = await draw_chart_info(songs[0], user)
    elif len(songs) <= 5:
        r = ""
        for song in songs:
            r += f"{f'「{song.song_id}」':<7} {song.song_name}\n"
        image = MessageSegment.text(r)
    else:
        image = draw_song_list(songs, page)
    await matcher.send(image, reply_message=True)


@search_alias_song.handle()
@search_alias_song_regex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=(1, 2))),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    parts = args.split()
    if not parts:
        await matcher.finish("请输入要查询的别名", reply_message=True)

    page = 1
    if len(parts) >= 2 and parts[-1].isdigit():
        name = " ".join(parts[:-1])
        page = int(parts[-1])
    else:
        name = " ".join(parts)

    error_msg = f"未找到别名为「{name}」的歌曲"
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        try:
            api = YuzuChaNAPI()
            obj = await api.get_songs(name)
        except Exception:
            obj = None
        if (
            isinstance(obj, Songs)
            and obj.type == StatusEnum.ONGOING
            and obj.data
            and isinstance(obj.data[0], AliasStatus)
        ):
            msg = f"未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n"
            for _s in obj.data:
                msg += f"- {_s.tag}\n    ID {_s.song_id}: {_s.name}\n"
            msg += "※ 可以使用指令「同意别名 XXXXX」进行投票"
            await matcher.finish(msg.strip(), reply_message=True)
        elif isinstance(obj, Songs):
            alias_data = yuzu_alias_to_alias(obj.data)

    if alias_data:
        if len(alias_data) != 1:
            msg = f"找到{len(alias_data)}个相同别名的曲目：\n"
            for song in alias_data:
                msg += f"{song.song_id}：{song.song_name}\n"
            msg += "※ 请使用「/id xxxxx」查询指定曲目"
            await matcher.finish(msg.strip(), reply_message=True)
        else:
            song = mai.total_list.by_id(alias_data[0].song_id)
            if song:
                msg = "您要找的是不是：" + await draw_chart_info(song, user)
            else:
                msg = error_msg
            await matcher.finish(msg, reply_message=True)

    # id
    if name.isdigit() and (song := mai.total_list.by_id(int(name))):
        await matcher.finish(
            "您要找的是不是：" + await draw_chart_info(song, user), reply_message=True
        )
    if search_id := re.search(r"^id([0-9]+)$", name, re.IGNORECASE):
        song = mai.total_list.by_id(int(search_id.group(1)))
        if not song:
            await matcher.finish(
                f"未找到ID「{search_id.group(1)}」的乐曲", reply_message=True
            )
        await matcher.finish(
            "您要找的是不是：" + await draw_chart_info(song, user), reply_message=True
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
        msg += draw_song_list(result, page)
    await matcher.finish(msg, reply_message=True)


@query_chart.handle()
@query_chart_regex.handle()
async def _(
    matcher: Matcher,
    song_id: str = Depends(UniCommand()),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    if not song_id.isdigit():
        await matcher.finish("请输入正确的曲目ID", reply_message=True)

    song = mai.total_list.by_id(int(song_id))
    if not song:
        msg = f"未找到ID「{song_id}」的乐曲"
    else:
        msg = await draw_chart_info(song, user)
    await matcher.finish(msg, reply_message=True)
