import random
import re
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.params import CommandArg, Depends
from PIL import Image

from ..config import log, lxnsconfig, maiconfig
from ..constants import FORTUNE, LEVEL_LIST
from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, update_user
from ..core.image.tools import image_to_bytesio, song_chart
from ..core.merge.models.theme import Theme
from ..core.search import (
    bind_lxns,
    draw_chart_info,
    draw_rating_ranking,
    draw_rise_score_list,
)
from ..core.service import mai
from ..core.tool import qqhash
from ..resources import Root
from .extra import get_optional_user, get_user_db

CODE_PATTERN = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$')

AUTHORIZE_URL = (
    'https://maimai.lxns.net/oauth/authorize'
    '?response_type=code'
    f'&client_id={lxnsconfig.lx_client_id}'
    f'&redirect_uri={lxnsconfig.redirect_uri}'
    f'&scope=read_player+read_user_profile+write_player'
)
AUTHORIZE_ERROR = (
    f'您尚未授权「{maiconfig.bot_name} BOT」'
    '访问您的落雪查分器数据，请先使用「/绑定落雪」指令进行绑定。'
)
AUTHORIZE_MSG = dedent(f'''
    请点击以下链接进行授权
    允许「{maiconfig.bot_name} BOT」访问您的落雪查分器数据
    =======================
    {AUTHORIZE_URL}
    =======================
    点击授权后您应收到该格式的
    授权码：「XXXX-XXXX-XXXX」
    请复制该授权码，并使用「/授权码」指令进行授权
    =======================
    请注意！！您必须在落雪查分器的
    「账号设置 -> 常规设置」中的
    「隐私设置」开启允许读取成绩，否
    则BOT将无法查询您的成绩
''').strip()


bind            = on_command("绑定")
bindlx          = on_command("绑定落雪")
auth            = on_command("授权码")
guildid         = on_command("频道ID")
theme           = on_command("主题")
help            = on_command("help")
portune         = on_command("今日舞萌")
random_song     = on_command("随机谱面")
rise_score      = on_command("我要上分")
rating_ranking  = on_command("查看排名")


@bind.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    qqid = message.extract_plain_text().strip()
    open_id = event.author.member_openid
    try:
        if qqid.isdigit():
            await update_user(open_id, qqid=qqid)
            await bind.send(F"已绑定QQ {qqid}")
        else:
            await bind.send("QQ号格式错误，请重新绑定")
    except UserNotBindError:
        await update_user(open_id, qqid=qqid)
        await bind.send(F"已绑定QQ {qqid}")


@bindlx.handle()
async def _(event: GroupAtMessageCreateEvent):
    await bindlx.send(AUTHORIZE_MSG)


@auth.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    code = message.extract_plain_text().strip()
    if not CODE_PATTERN.fullmatch(code):
        await auth.reject('授权码格式错误，请重新发送。')
    result = await bind_lxns(user, code)
    await auth.send(result)


@guildid.handle()
async def _(event: AtMessageCreateEvent | DirectMessageCreateEvent):
    open_id = event.author.id
    if isinstance(event, AtMessageCreateEvent):
        await guildid.send(
            MessageSegment.mention_user(open_id) + 
            f"您的频道ID为：{open_id}\n现在可前往查分器官网进行频道绑定"
        )
    else:
        await guildid.send(f"您的频道ID为：{open_id}\n现在可前往查分器官网进行频道绑定")


@theme.handle()
async def _(
    message: Message = CommandArg(), 
    user: User = Depends(get_user_db)
):
    args = message.extract_plain_text().strip()
    theme_ = Theme.get_by_index(args)
    if theme_ is None:
        await theme.finish(f"未找到该主题：\n{Theme.get_help()}")
    
    await update_user(user.open_id, theme=theme_)
    await theme.send(f"主题已切换为：「{theme_.value}」")


@help.handle()
async def _(event: MessageEvent):
    await help.send(
        MessageSegment.file_image(image_to_bytesio(Image.open(Root / "maimaidxhelp.png")))
    )


@portune.handle()
async def _(user: User = Depends(get_user_db)):
    h = qqhash(user.qqid)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f"\n今日人品值：{rp}\n"
    for i in range(11):
        if wm_value[i] == 3:
            msg += f"宜 {FORTUNE[i]}\n"
        elif wm_value[i] == 0:
            msg += f"忌 {FORTUNE[i]}\n"
    music = mai.total_list.root[h % len(mai.total_list.root)]
    ds = "/".join([str(d.level_value) for d in music.difficulties])
    msg += (
        f"{maiconfig.bot_name} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
        f"ID.{music.song_id} - {music.song_name}"
        f"{MessageSegment.file_image(song_chart(music.song_id))}"
        f"{ds}"
    )
    await portune.send(msg)


@random_song.handle()
async def _(message: Message = CommandArg(), user: User | None = Depends(get_optional_user)):
    args = message.extract_plain_text().strip()
    match = re.search(r"^((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$", args)
    if not match:
        await random_song.finish("参数错误，请重新发送随机谱面")
    diff = match.group(1)
    if diff == "dx":
        type_ = ["DX"]
    elif diff == "sd" or diff == "标准":
        type_ = ["SD"]
    else:
        type_ = ["SD", "DX"]
    level = match.group(3)
    if match.group(2) == "":
        songs = mai.total_list.filter(level=level, type=type_)
    else:
        songs = mai.total_list.filter(
            level=level, 
            type=type_
        )
    if len(songs) == 0:
        result = "没有这样的乐曲哦。"
    else:
        result = await draw_chart_info(random.choice(songs), user)
    await random_song.send(result)


@rise_score.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    args = message.extract_plain_text().strip()
    match = re.search(r"^([0-9]+\+?)?\+([0-9]+)$", args)
    if not match:
        rating = None
        score = None
    else:
        rating = match.group(1)
        score = int(match.group(2))
    
    if rating and rating not in LEVEL_LIST:
        await rise_score.finish("无此等级")

    data = await draw_rise_score_list(user, None, rating, score)
    await rise_score.send(data)


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
    await rating_ranking.send(pic)


async def update_daily():
    await mai.get_music()
    log.info("maimaiDX数据更新完毕")

async def update_daily():
    await mai.get_music()
    log.info("maimaiDX数据更新完毕")