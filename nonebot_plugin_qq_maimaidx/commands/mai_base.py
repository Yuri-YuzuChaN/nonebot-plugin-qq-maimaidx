import random
import re

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

from ..config import log, maiconfig
from ..constants import LEVEL_LIST
from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user, update_user
from ..core.image.tools import image_to_bytesio, song_chart
from ..core.search import draw_chart_info, draw_rating_ranking, draw_rise_score_list
from ..core.service import mai
from ..core.tool import qqhash
from ..resources import Root
from .extra import get_user_db

bind            = on_command("绑定")
guildid         = on_command("频道ID")
theme           = on_command("主题")
help            = on_command("help")
mai_today       = on_command("今日舞萌")
random_song     = on_command("随机谱面")
rise_score      = on_command("我要上分")
rating_ranking  = on_command("查看排名")


@bind.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    qqid = message.extract_plain_text().strip()
    open_id = event.author.member_openid
    try:
        if qqid.isdigit() and await get_user(open_id):
            await update_user(open_id, qqid)
            await bind.send(F"已绑定QQ {qqid}")
        else:
            await bind.send("QQ号格式错误，请重新绑定")
    except UserNotBindError:
        await update_user(open_id, qqid=qqid)
        await bind.send(F"已绑定QQ {qqid}")


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
    event: AtMessageCreateEvent | DirectMessageCreateEvent, 
    user: User = Depends(get_user_db)
):
    await update_user()
    


@help.handle()
async def _(event: MessageEvent):
    await help.send(
        MessageSegment.file_image(image_to_bytesio(Image.open(Root / "maimaidxhelp.png")))
    )


@mai_today.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    user: User | None = Depends(get_user_db)
):
    if user is None:
        await mai_today.finish()
    wm_list = [
        "拼机", 
        "推分", 
        "越级", 
        "下埋", 
        "夜勤", 
        "练底力", 
        "练手法", 
        "打旧框", 
        "干饭", 
        "抓绝赞", 
        "收歌"
    ]
    h = qqhash(user.qqid)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f"\n今日人品值：{rp}\n"
    for i in range(11):
        if wm_value[i] == 3:
            msg += f"宜 {wm_list[i]}\n"
        elif wm_value[i] == 0:
            msg += f"忌 {wm_list[i]}\n"
    music = mai.total_list.root[h % len(mai.total_list.root)]
    ds = "/".join([str(d.level_value) for d in music.difficulties])
    msg += (
        f"{maiconfig.bot_name} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
        f"ID.{music.song_id} - {music.song_name}"
        f"{MessageSegment.file_image(song_chart(music.song_id))}"
        f"{ds}"
    )
    await mai_today.send(msg)
        
        
@random_song.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user: User = Depends(get_user_db)
):
    args = message.extract_plain_text().strip()
    match = re.search(r"^((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$", args)
    if not match:
        await random_song.finish("参数错误，请重新发送随机谱面")
    diff = match.group(1)
    if diff == "dx":
        tp = ["DX"]
    elif diff == "sd" or diff == "标准":
        tp = ["SD"]
    else:
        tp = ["SD", "DX"]
    level = match.group(3)
    if match.group(2) == "":
        songs = mai.total_list.filter(level=level, type=tp)
    else:
        songs = mai.total_list.filter(
            level=level, 
            type=tp
        )
    if len(songs) == 0:
        result = "没有这样的乐曲哦。"
    else:
        result = await draw_chart_info(random.choice(songs), user)
    await random_song.send(result)


@rise_score.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg(), 
    user: User = Depends(get_user_db)
):
    if user is None:
        await rise_score.finish()
    
    args = message.extract_plain_text().strip()
    match = re.search(r"^([0-9]+\+?)?\+([0-9]+)$", args)
    if not match:
        rating = None
        score = None
    else:
        rating = match.group(1)
        score = int(match.group(2))
    
    if rating and rating not in LEVEL_LIST:
        await rise_score.finish("无此等级", reply_message=True)

    data = await draw_rise_score_list(user, None, rating, score)
    await rise_score.send(data)


@rating_ranking.handle()
async def _(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent, 
    message: Message = CommandArg()
):
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