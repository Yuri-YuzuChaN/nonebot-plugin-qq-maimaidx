import re
from typing import Union

from nonebot import on_command
from nonebot.adapters.qq import AtMessageCreateEvent, GroupAtMessageCreateEvent, Message
from nonebot.params import CommandArg

from ..libraries.maimaidx_music import mai

alias_song = on_command('查询别名', priority=5)


@alias_song.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    match = re.search(r'^(id)?\s?(.+)', args, re.IGNORECASE)
    if not match:
        await alias_song.finish('指令错误，请重新输入')
    isid = match.group(1)
    name = match.group(2)
    if isid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(name)
        if not alias_id:
            await alias_song.finish('未找到此歌曲')
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(name)
                if not alias_id:
                    await alias_song.finish('未找到此歌曲')
                else:
                    aliases = alias_id
            else:
                await alias_song.finish('未找到此歌曲')
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = '\n'.join(songs.Alias)
            msg.append(f'ID：{songs.SongID}\n{alias_list}')
        await alias_song.finish(f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg))

    if len(aliases[0].Alias) == 1:
        await alias_song.finish('该曲目没有别名')

    msg = f'该曲目有以下别名：\nID：{aliases[0].SongID}\n'
    msg += '\n'.join(aliases[0].Alias)
    await alias_song.send(msg)