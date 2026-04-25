from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.qq import AtMessageCreateEvent, GroupAtMessageCreateEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends

from ..core.clients.exceptions import UserNotBindError
from ..core.clients.lxns.models.oauth import BaseToken
from ..core.database.qq import User
from ..core.merge.models.service import ServiceName
from ..core.search import draw_best50, draw_play_data, draw_song_galobal_data
from ..core.service import mai
from .extra import get_user_db

dfb50   = on_command("b50")
lxb50   = on_command("lx50")
info    = on_command("info")
dfinfo  = on_command("dfinfo")
lxinfo  = on_command("lxinfo")
ginfo   = on_command("ginfo")


@dfb50.handle()
@lxb50.handle()
async def _(
    matcher: Matcher,
    event: AtMessageCreateEvent | GroupAtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user: User = Depends(get_user_db)
):
    try:
        username = message.extract_plain_text().strip()
        icon = None
        if isinstance(event, AtMessageCreateEvent) and not username:
            icon = event.author.avatar
        if isinstance(matcher, dfb50):
            result = await draw_best50(
                user, 
                username=username, 
                icon=icon
            )
        else:
            result = await draw_best50(user)
    except UserNotBindError as e:
        result = str(e)
    await matcher.send(result)


@info.handle()
@dfinfo.handle()
@lxinfo.handle()
async def _(
    matcher: Matcher,
    event: AtMessageCreateEvent | GroupAtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user: User = Depends(get_user_db)
):
    data = message.extract_plain_text().strip()
    if not data:
        await matcher.finish("请输入曲目id或曲名")
    
    if data.isdigit() and mai.total_list.by_id(int(data)):
        song_id = data
    elif by_t := mai.total_list.by_name(data):
        song_id = by_t.song_id
    else:
        aliases = mai.total_alias_list.by_alias(data)
        if not aliases:
            await matcher.finish("未找到曲目")
        elif len(aliases) != 1:
            msg = "找到相同别名的曲目，请使用以下ID查询：\n"
            for alias in aliases:
                msg += f"{alias.song_id}：{alias.alias[0]}\n"
            await matcher.finish(msg.strip())
        else:
            song_id = aliases[0].song_id
    song = mai.total_list.by_id(int(song_id))
    
    if isinstance(matcher, info):
        service = None
    elif isinstance(matcher, dfinfo):
        service = ServiceName.DIVINGFISH
    else:
        service = ServiceName.LXNS
    result = await draw_play_data(user, song, service=service)
    await matcher.send(result)


@ginfo.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    if not args:
        await ginfo.finish("请输入曲目id或曲名")
    if args[0] not in "绿黄红紫白":
        level_index = 3
    else:
        level_index = "绿黄红紫白".index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish("请输入曲目id或曲名")
    if mai.total_list.by_id(args):
        id = args
    elif by_t := mai.total_list.by_name(args):
        id = by_t.song_id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            await ginfo.finish("未找到曲目")
        elif len(alias) != 1:
            msg = "找到相同别名的曲目，请使用以下ID查询：\n"
            for songs in alias:
                msg += f"{songs.song_id}：{songs.alias[0]}\n"
            await ginfo.finish(msg.strip())
        else:
            id = str(alias[0].song_id)
    
    song = mai.total_list.by_id(id)
    stats = song.difficulties[level_index].stats
    
    if len(song.difficulties) == 4 and level_index == 4:
        await ginfo.finish("该乐曲没有这个等级")
    if not song.difficulties[level_index]:
        await ginfo.finish("该等级没有统计信息")

    data = await draw_song_galobal_data(song, level_index) + dedent(f"""\
        游玩次数：{round(stats.cnt)}
        拟合难度：{stats.fit_diff:.2f}
        平均达成率：{stats.avg:.2f}%
        平均 DX 分数：{stats.avg_dx:.1f}
        谱面成绩标准差：{stats.std_dev:.2f}""")
    await ginfo.send(data)