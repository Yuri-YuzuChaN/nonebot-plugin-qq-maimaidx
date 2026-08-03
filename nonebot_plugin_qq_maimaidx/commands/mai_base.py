import random
import re

from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    GroupMessageCreateEvent,
    Message,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends, RegexMatched

from ..config import lxnsconfig, maiconfig
from ..constants import FORTUNE, LEVEL_LIST
from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, update_user
from ..core.handler import (
    bind_lxns,
    draw_chart_info,
    draw_rating_ranking,
    draw_rise_score_list,
    get_mai_what,
)
from ..core.image import UpdateTable
from ..core.image.tools import song_chart
from ..core.merge.models import ServiceName, Theme
from ..core.service import mai
from ..core.tool import qqhash
from ..markdown.auth import auth_md
from ..resources import Root
from .depend import GetOrCreateUser, GetUserAndAuth, GetUserAndAuthOrNone, UniCommand
from .router import on_command, on_regex

CODE_PATTERN = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
RANDOM_SONG_PATTERN = r"^((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$"
RANDOM_SONG_REGEX_PATTERN = r"^[随来给]个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?).*"
RISE_SCORE_PATTERN = r"^([0-9]+\+?)?\+([0-9]+)$"
RISE_SCORE_REGEX_PATTERN = r"^我要在?([0-9]+\+?)?[上加\+]([0-9]+)?分\s?(.+)?"

LXNS_ERROR = "BOT管理员尚未配置落雪查分器相关信息"


update = on_command("UPDATE_DATA")
bind = on_command("绑定")
bindlx = on_command("绑定落雪")
auth = on_command("授权码")
source = on_command("数据源")
guildid = on_command("频道ID")
theme = on_command("主题")
help = on_command("help")
portune = on_command("今日舞萌")
mai_what = on_regex(r".*mai.*什么(.+)?")
random_song = on_command("随机谱面")
random_song_regex = on_regex(RANDOM_SONG_REGEX_PATTERN, re.IGNORECASE)
rise_score = on_command("我要上分")
rise_score_regex = on_regex(RISE_SCORE_REGEX_PATTERN)
rating_ranking = on_command("查看排名")


@update.handle()
async def _():
    await update.send("正在进行更新...", reply_message=True)
    await mai.update()
    table = UpdateTable()
    await table.update_rating_table()
    await table.update_level_15_rating_table()
    await table.update_plate_table()
    await table.update_wu_plate_table()
    await update.finish("更新完成。", reply_message=True)


@bind.handle()
async def _(
    event: GroupAtMessageCreateEvent | GroupMessageCreateEvent,
    message: Message = CommandArg(),
):
    qqid = message.extract_plain_text().strip()
    user_id = event.author.member_openid
    try:
        if qqid.isdigit():
            await update_user(user_id, qqid=int(qqid))
            await bind.send(f"已绑定QQ {qqid}", reply_message=True)
        else:
            await bind.send("QQ号格式错误，请重新绑定", reply_message=True)
    except UserNotBindError:
        await update_user(user_id, qqid=qqid)
        await bind.send(f"已绑定QQ {qqid}", reply_message=True)


@bindlx.handle()
async def _():
    await bindlx.send(auth_md, reply_message=True)


@auth.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetOrCreateUser)):
    code = message.extract_plain_text().strip()
    if not CODE_PATTERN.fullmatch(code):
        await auth.reject("授权码格式错误，请重新发送。", reply_message=True)
    result = await bind_lxns(user, code)
    await auth.send(result, reply_message=True)


@source.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetOrCreateUser)):
    args = message.extract_plain_text().strip()
    source_ = ServiceName.get_by_index(args)
    if source_ is None:
        await source.finish(
            f"未找到该数据源：\n{ServiceName.get_help()}", reply_message=True
        )
    if (
        source_ == ServiceName.LXNS
        and lxnsconfig.lxns_dev_token is None
        and (lxnsconfig.lx_client_id is None or lxnsconfig.redirect_uri is None)
    ):
        await update_user(user.user_id, service=ServiceName.DIVINGFISH)
        await source.finish(
            LXNS_ERROR + "。为防止无法查询成绩，已强制将数据源切换为水鱼查分器。",
            reply_message=True,
        )

    await update_user(user.user_id, service=source_)
    await source.send(f"数据源已切换为：「{source_.value}」", reply_message=True)


@guildid.handle()
async def _(event: AtMessageCreateEvent | DirectMessageCreateEvent):
    open_id = event.author.id
    if isinstance(event, AtMessageCreateEvent):
        await guildid.send(
            MessageSegment.mention_user(open_id)
            + f"您的频道ID为：{open_id}\n现在可前往查分器官网进行频道绑定",
            reply_message=True,
        )
    else:
        await guildid.send(
            f"您的频道ID为：{open_id}\n现在可前往查分器官网进行频道绑定",
            reply_message=True,
        )


@theme.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetOrCreateUser)):
    args = message.extract_plain_text().strip()
    theme_ = Theme.get_by_index(args)
    if theme_ is None:
        await theme.finish(f"未找到该主题：\n{Theme.get_help()}", reply_message=True)

    await update_user(user.user_id, theme=theme_)
    await theme.send(f"主题已切换为：「{theme_.value}」", reply_message=True)


@help.handle()
async def _():
    await help.send(
        MessageSegment.file_image(Root / "maimaidxhelp.png"), reply_message=True
    )


@portune.handle()
async def _(user: User | None = Depends(GetOrCreateUser)):
    if user.qqid is None:
        await portune.finish("请先使用「/绑定」指令绑定QQ。", reply_message=True)
    fortune_hash = qqhash(user.qqid)
    daily_random = random.Random(fortune_hash)
    rp = fortune_hash % 100
    h = fortune_hash
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f"今日人品值：{rp}\n"
    for i in range(11):
        if wm_value[i] == 3:
            msg += f"宜 {FORTUNE[i]}\n"
        elif wm_value[i] == 0:
            msg += f"忌 {FORTUNE[i]}\n"
    song = daily_random.choice(mai.total_list.root)
    ds = "/".join([str(d.level_value) for d in song.difficulties])
    result = (
        MessageSegment.text(
            msg
            + f"{maiconfig.bot_name} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
            + f"ID.{song.song_id} - {song.song_name}"
        )
        + MessageSegment.file_image(song_chart(song.song_id))
        + MessageSegment.text(ds)
    )
    await portune.send(result, reply_message=True)


@mai_what.handle()
async def _(
    match: re.Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    song = mai.total_list.random()
    if (
        (point := match.group(1))
        and ("推分" in point or "上分" in point or "加分" in point)
        and user
    ):
        _song = await get_mai_what(user)
        if _song is not None:
            song = _song
    await mai_what.finish(await draw_chart_info(song, user), reply_message=True)


@random_song.handle()
@random_song_regex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=0)),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    match = re.search(RANDOM_SONG_REGEX_PATTERN, args, re.IGNORECASE)
    if not match:
        match = re.search(RANDOM_SONG_PATTERN, args, re.IGNORECASE)
    if not match:
        await matcher.finish("参数错误，请重新发送随机谱面", reply_message=True)
    diff = (match.group(1) or "").lower()
    if diff == "dx":
        type_ = ["DX"]
    elif diff == "sd" or diff == "标准":
        type_ = ["SD"]
    else:
        type_ = ["SD", "DX"]
    level = match.group(3)
    color = match.group(2)
    songs = mai.total_list.filter(level=level, type=type_)
    if color:
        ci = "绿黄红紫白".index(color)
        songs = [
            s
            for s in songs
            if len(s.difficulties) > ci and s.difficulties[ci].level == level
        ]
    if len(songs) == 0:
        result = "没有这样的乐曲哦。"
    else:
        result = await draw_chart_info(random.choice(songs), user)
    await matcher.send(result, reply_message=True)


@rise_score.handle()
@rise_score_regex.handle()
async def _(
    matcher: Matcher,
    args: str = Depends(UniCommand(regex_group=0)),
    user: User = Depends(GetUserAndAuth),
):
    match = re.search(RISE_SCORE_REGEX_PATTERN, args)
    if not match:
        match = re.search(RISE_SCORE_PATTERN, args)
    if not match:
        rating = None
        score = None
    else:
        rating = match.group(1)
        score = int(match.group(2)) if match.group(2) else None

    if rating and rating not in LEVEL_LIST:
        await matcher.finish("无此等级", reply_message=True)

    data = await draw_rise_score_list(user, rating, score)
    await matcher.send(data, reply_message=True)


@rating_ranking.handle()
async def _(message: Message = CommandArg()):
    name = ""
    page = 1
    args = message.extract_plain_text().strip()
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()
    pic = await draw_rating_ranking(name, page)
    await rating_ranking.send(pic, reply_message=True)
