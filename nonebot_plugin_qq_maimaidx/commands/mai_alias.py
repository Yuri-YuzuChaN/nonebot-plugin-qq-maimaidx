import re

from nonebot import on_command
from nonebot.adapters.qq import Message
from nonebot.params import CommandArg

from ..core.service import mai

alias_song = on_command("查询别名")


@alias_song.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    match = re.search(r"^(id(?=[\s0-9]))?\s?(.+)", args, re.IGNORECASE)
    if not match:
        await alias_song.finish("指令错误，请重新输入")
    findid = bool(match.group(1))
    name = match.group(2)
    aliases = None
    if findid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(int(name))
        if not alias_id:
            await alias_song.finish(
                "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名"
            )
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(int(name))
                if not alias_id:
                    await alias_song.finish(
                        "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名"
                    )
                else:
                    aliases = alias_id
            else:
                await alias_song.finish(
                    "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名"
                )
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = "\n".join(songs.alias)
            msg.append(f"ID：{songs.song_id}\n{alias_list}")
        await alias_song.finish(
            f"找到{len(aliases)}个相同别名的曲目：\n" + "\n======\n".join(msg),
        )

    real_aliases = [
        a for a in aliases[0].alias if a.lower() != aliases[0].song_name.lower()
    ]
    if not real_aliases:
        await alias_song.finish("该曲目没有别名")

    msg = f"该曲目有以下别名：\nID：{aliases[0].song_id}\n"
    msg += "\n".join(real_aliases)
    await alias_song.send(msg)
