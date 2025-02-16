import re
from typing import Union

from nonebot import on_command
from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    Message,
    MessageSegment,
)
from nonebot.params import CommandArg, Depends

from ..config import Root, levelList, log, maiconfig
from ..libraries.image import music_picture
from ..libraries.maimaidx_database import get_user, insert_user, update_user
from ..libraries.maimaidx_error import UserNotBindError
from ..libraries.maimaidx_music import mai
from ..libraries.maimaidx_music_info import draw_music_info
from ..libraries.maimaidx_player_score import rating_ranking_data, rise_score_data
from ..message import image, send_image

bind            = on_command('绑定')
guildid         = on_command('频道ID')
help            = on_command('help')
mai_today       = on_command('今日舞萌')
random_song     = on_command('随机谱面')
rise_score      = on_command('我要上分')
rating_ranking  = on_command('查看排名')


def get_qqid(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent, DirectMessageCreateEvent]) -> str:
    if isinstance(event, GroupAtMessageCreateEvent):
        return event.author.member_openid
    else:
        return event.author.id


@bind.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    try:
        qqid = message.extract_plain_text().strip()
        user_id = event.author.member_openid
        if qqid.isdigit() and get_user(user_id):
            update_user(user_id, qqid)
            await bind.send(F'已绑定QQ {qqid}')
        else:
            await bind.send('QQ号格式错误，请重新绑定')
    except UserNotBindError:
        insert_user(user_id, qqid)
        await bind.send(F'已绑定QQ {qqid}')


@guildid.handle()
async def _(event: Union[AtMessageCreateEvent, DirectMessageCreateEvent]):
    user_id = event.author.id
    if isinstance(event, AtMessageCreateEvent):
        await guildid.send(MessageSegment.mention_user(user_id) + f'您的频道ID为：{user_id}\n现在可前往查分器官网进行频道绑定')
    else:
        await guildid.send(f'您的频道ID为：{user_id}\n现在可前往查分器官网进行频道绑定')


@help.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent]):
    await send_image(help, event=event, data=Root / 'maimaidxhelp.png')


@mai_today.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
        wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌']
        h = hash(int(user_id))
        rp = h % 100
        wm_value = []
        for i in range(11):
            wm_value.append(h & 3)
            h >>= 2
        msg = f'\n今日人品值：{rp}\n'
        for i in range(11):
            if wm_value[i] == 3:
                msg += f'宜 {wm_list[i]}\n'
            elif wm_value[i] == 0:
                msg += f'忌 {wm_list[i]}\n'
        music = mai.total_list[h % len(mai.total_list)]
        ds = '/'.join([str(_) for _ in music.ds])
        msg += f'{maiconfig.botName} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲：'
        msg += f'ID.{music.id} - {music.title}'
        msg += await image(event, music_picture(music.id))
        msg += ds
        await send_image(mai_today, msg)
    except UserNotBindError as e:
        await mai_today.send(str(e))
        
        
@random_song.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError:
        user_id = None
    args = message.extract_plain_text().strip()
    match = re.search(r'^((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$', args)
    if not match:
        await random_song.finish('参数错误，请重新发送随机谱面')
    diff = match.group(1)
    if diff == 'dx':
        tp = ['DX']
    elif diff == 'sd' or diff == '标准':
        tp = ['SD']
    else:
        tp = ['SD', 'DX']
    level = match.group(3)
    if match.group(2) == '':
        music_data = mai.total_list.filter(level=level, type=tp)
    else:
        music_data = mai.total_list.filter(level=level, diff=['绿黄红紫白'.index(match.group(2))], type=tp)
    if len(music_data) == 0:
        await random_song.finish('没有这样的乐曲哦。')
    pic = await draw_music_info(music_data.random(), user_id)
    await send_image(random_song, event=event, data=pic)


@rise_score.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg(), user_id: str = Depends(get_qqid)):
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = get_user(user_id).QQID
    except UserNotBindError as e:
        await rise_score.finish(str(e))
    
    args = message.extract_plain_text().strip()
    match = re.search(r'^([0-9]+\+?)?\+([0-9]+)$', args)
    if not match:
        rating = None
        score = None
    else:
        rating = match.group(1)
        score = int(match.group(2))
    
    if rating and rating not in levelList:
        await rise_score.finish('无此等级', reply_message=True)

    data = await rise_score_data(user_id, None, rating, score)
    if isinstance(data, str):
        await rise_score.finish(data)
    await send_image(rise_score, event=event, data=data)


@rating_ranking.handle()
async def _(event: Union[GroupAtMessageCreateEvent, AtMessageCreateEvent], message: Message = CommandArg()):
    name = ''
    page = 1
    args = message.extract_plain_text().strip()
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()
    pic = await rating_ranking_data(name, page)
    await send_image(rating_ranking, event=event, data=pic)
    

async def data_update_daily():
    await mai.get_music()
    log.info('maimaiDX数据更新完毕')