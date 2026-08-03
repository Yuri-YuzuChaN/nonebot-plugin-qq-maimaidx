import re

from nonebot.matcher import Matcher
from nonebot.params import Depends

from ..core.service import mai
from .depend import UniCommand
from .router import on_command, on_regex

alias_song = on_command("查询别名")
alias_song_rex = on_regex(r"^(id(?=\s|\d))?\s*(.+?)\s*有什么别[名称]$", re.IGNORECASE)


@alias_song.handle()
@alias_song_rex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=(1, 2))),
):
    match = re.fullmatch(r"(id(?=\s|\d))?\s*(.+?)\s*", args, re.IGNORECASE)
    if not match:
        await matcher.finish("指令错误，请重新输入", reply_message=True)
    findid = bool(match.group(1))
    name = match.group(2).strip()
    aliases = None
    if findid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(int(name))
        if not alias_id:
            await matcher.finish(
                "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                reply_message=True,
            )
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(int(name))
                if not alias_id:
                    await matcher.finish(
                        "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                        reply_message=True,
                    )
                else:
                    aliases = alias_id
            else:
                await matcher.finish(
                    "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                    reply_message=True,
                )
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = "\n".join(songs.alias)
            msg.append(f"ID：{songs.song_id}\n{alias_list}")
        await matcher.finish(
            f"找到{len(aliases)}个相同别名的曲目：\n" + "\n======\n".join(msg),
            reply_message=True,
        )

    real_aliases = [
        a for a in aliases[0].alias if a.lower() != aliases[0].song_name.lower()
    ]
    if not real_aliases:
        await matcher.finish("该曲目没有别名", reply_message=True)

    msg = f"该曲目有以下别名：\nID：{aliases[0].song_id}\n"
    msg += "\n".join(real_aliases)
    await matcher.send(msg, reply_message=True)
