import re
from pathlib import Path
from random import sample
from string import ascii_uppercase, digits
from textwrap import dedent

import nonebot
from nonebot import on_command, require
from nonebot.adapters.qq import GroupAtMessageCreateEvent, Message, MessageSegment
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .config import *
from .libraries.maimaidx_database import *
from .libraries.maimaidx_music import mai, update_local_alias
from .libraries.maimaidx_music_info import *
from .libraries.maimaidx_player_score import *
from .libraries.tool import hash
from .web import *

__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-qq-maimaidx',
    description='移植自 mai-bot 开源项目，基于 nonebot2 的街机音游 舞萌DX 的查询插件',
    usage='请使用 帮助maimaiDX 指令查看使用方法',
    type='application',
    config=Config,
    homepage='https://github.com/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx',
    supported_adapters={'~qq'}
)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath('plugins').resolve())
)

scheduler = require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler

bind = on_command('绑定', priority=5)
data_update = on_command('更新maimai数据', priority=5, permission=SUPERUSER)
manual = on_command('help', priority=5)
search_base = on_command('定数查歌', priority=5)
search_bpm = on_command('bpm查歌', priority=5)
search_artist = on_command('曲师查歌', priority=5)
search_charter = on_command('谱师查歌', priority=5)
random_song = on_command('随机谱面', priority=5)
mai_what = on_command('mai什么', priority=5)
search = on_command('查歌', priority=5)  # 注意 on 响应器的注册顺序，search 应当优先于 search_* 之前注册
query_chart = on_command('id', priority=5)
mai_today = on_command('今日舞萌', priority=5)
what_song = on_command('别名查歌', priority=5)
alias_song = on_command('查询别名', priority=5)
alias_local_apply = on_command('添加本地别名', priority=5)
alias_apply = on_command('添加别名', priority=5)
alias_agree = on_command('同意别名', priority=5)
alias_status = on_command('当前投票', priority=5)
alias_update = on_command('更新别名库', priority=5, permission=SUPERUSER)
score = on_command('分数线', priority=5)
best50 = on_command('b50', priority=5)
minfo = on_command('minfo', priority=5)
ginfo = on_command('ginfo', priority=5)
table_update = on_command('更新定数表', priority=5, permission=SUPERUSER)
plate_update = on_command('更新完成表', priority=5, permission=SUPERUSER)
rating_table = on_command('定数表', priority=5)
rating_table_pf = on_command('完成表', priority=5)
rise_score = on_command('上分', priority=5)
plate_process = on_command('牌子进度', priority=5)
level_process = on_command('等级进度', priority=5)
level_achievement_list = on_command('分数列表', priority=5)
rating_ranking = on_command('查看排名', priority=5)


def song_level(ds1: float, ds2: float, stats1: str = None, stats2: str = None) -> List[Tuple[str, str, float, str, str]]:
    result = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    music_data.sort(key=lambda i: int(i.id))
    if stats1:
        if stats2:
            stats1 = stats1 + ' ' + stats2
            stats1 = stats1.title()
        for music in music_data:
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    else:
        for music in music_data:
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    return result


def get_user_id(event: GroupAtMessageCreateEvent) -> str:
    return event.author.member_openid


def get_qqid(event: GroupAtMessageCreateEvent) -> int:
    return get_user(event.author.member_openid).QQID


@driver.on_startup
async def get_music():
    """
    bot启动时开始获取所有数据
    """
    maiApi.load_token()
    log.info('正在获取maimai所有曲目信息')
    await mai.get_music()
    log.info('正在获取maimai所有曲目别名信息')
    await mai.get_music_alias()
    log.success('maimai数据获取完成')


@bind.handle()
async def _(args: Message = CommandArg(), user_id: str = Depends(get_user_id)):
    qqid = args.extract_plain_text().strip()
    try:
        if qqid.isdigit() and get_user(user_id):
            update_user(user_id, qqid)
            await bind.send(F'已绑定QQ {qqid}')
        else:
            await bind.send('QQ号格式错误，请重新绑定')
    except UserNotBindError:
        insert_user(user_id, qqid)
        await bind.send(F'已绑定QQ {qqid}')

@data_update.handle()
async def _():
    await mai.get_music()
    await mai.get_music_alias()
    await data_update.send('maimai数据更新完成')


@manual.handle()
async def _(event: GroupAtMessageCreateEvent):
    await manual.finish(MessageSegment.image(FileServer + '/help/maimaidxhelp.png'))


@search_base.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg()):
    args = args.extract_plain_text().strip().split()
    if len(args) > 4 or len(args) == 0:
        await search_base.finish('命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>')
    if len(args) == 1:
        result = song_level(float(args[0]), float(args[0]))
    elif len(args) == 2:
        try:
            result = song_level(float(args[0]), float(args[1]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]))
    elif len(args) == 3:
        try:
            result = song_level(float(args[0]), float(args[1]), str(args[2]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]), str(args[2]))
    else:
        result = song_level(float(args[0]), float(args[1]), str(args[2]), str(args[3]))
    if not result:
        await search_base.finish('没有找到这样的乐曲。')
    if len(result) >= 60:
        await search_base.finish(f'结果过多（{len(result)} 条），请缩小搜索范围')
    msg = ''
    for i in result:
        msg += f'{i[0]}. {i[1]} {i[3]} {i[4]}({i[2]})\n'
    await search_base.send(MessageSegment.image(await image_to_save(text_to_image(msg))))


@search_bpm.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg()):
    args = args.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        music_data = mai.total_list.filter(bpm=int(args[0]))
    elif len(args) == 2:
        music_data = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
    elif len(args) == 3:
        music_data = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
        page = int(args[2])
    else:
        await search_bpm.finish('命令格式为：\nbpm查歌 <bpm>\nbpm查歌 <bpm下限> <bpm上限> (<页数>)')
    if not music_data:
        await search_bpm.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    music_data.sort(key=lambda x: int(x.basic_info.bpm))
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} bpm {m.basic_info.bpm}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_bpm.send(MessageSegment.image(await image_to_save(text_to_image(msg))))


@search_artist.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)')
    else:
        name = ''
        await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)')
    if not name:
        return
    music_data = mai.total_list.filter(artist_search=name)
    if not music_data:
        await search_artist.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} {m.basic_info.artist}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_artist.send(MessageSegment.image(await image_to_save(text_to_image(msg))))


@search_charter.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)')
    else:
        name = ''
        await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)')
    if not name:
        return
    music_data = mai.total_list.filter(charter_search=name)
    if not music_data:
        await search_charter.finish('没有找到这样的乐曲。')
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            msg += f'No.{i + 1} {m.id}. {m.title} {" ".join([f"{d}/{c}" for d, c in diff_charter])}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_charter.send(MessageSegment.image(await image_to_save(text_to_image(msg))))


@random_song.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    try:
        args = message.extract_plain_text().strip()
        match = re.search(r'^((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$', args)
        if not match:
            return
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
            msg = '没有这样的乐曲哦。'
        else:
            msg = await new_draw_music_info(music_data.random())
    except:
        msg = '随机命令错误，请检查语法'
    await random_song.send(msg)


@mai_what.handle()
async def _(event: GroupAtMessageCreateEvent):
    await mai_what.finish(await new_draw_music_info(mai.total_list.random()))


@search.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        return
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search.send('没有找到这样的乐曲。')
    elif len(result) == 1:
        msg = await new_draw_music_info(result.random())
        await search.send(msg)
    elif len(result) < 50:
        search_result = ''
        result.sort(key=lambda i: int(i.id))
        for music in result:
            search_result += f'{music.id}. {music.title}\n'
        await search.send(MessageSegment.image(await image_to_save(text_to_image(search_result))))
    else:
        await search.send(f'结果过多（{len(result)} 条），请缩小查询范围。')


@query_chart.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg()):
    id = args.extract_plain_text().strip()
    music = mai.total_list.by_id(id)
    if not music:
        msg = f'未找到ID为[{id}]的乐曲'
    else:
        msg = await new_draw_music_info(music)
    await query_chart.send(msg)


@mai_today.handle()
async def _(event: GroupAtMessageCreateEvent, user_id: int = Depends(get_qqid)):
    try:
        wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌']
        h = hash(user_id)
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
        msg += f'{maiconfig.botName} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲：'
        music = mai.total_list[h % len(mai.total_list)]
        msg += await draw_music_info(music)
        await mai_today.send(msg)
    except UserNotBindError as e:
        await mai_today.send(str(e))


@alias_song.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    match = re.search(r'^(id)?\s?(.+)', args, re.IGNORECASE)
    if not match:
        await alias_song.finish('指令错误，请重新输入')
    isid = match.group(1)
    name = match.group(2)
    if isid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(name)
        if not alias_id:
            await alias_song.finish('未找到此歌曲\n可以使用 添加别名 指令给该乐曲添加别名')
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(name)
                if not alias_id:
                    await alias_song.finish('未找到此歌曲\n可以使用 添加别名 指令给该乐曲添加别名')
                else:
                    aliases = alias_id
            else:
                await alias_song.finish('未找到此歌曲\n可以使用 添加别名 指令给该乐曲添加别名')
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = '\n'.join(songs.Alias)
            msg.append(f'ID：{songs.ID}\n{alias_list}')
        await alias_song.finish(f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg))

    if len(aliases[0].Alias) == 1:
        await alias_song.finish('该曲目没有别名')

    msg = f'该曲目有以下别名：\nID：{aliases[0].ID}\n'
    msg += '\n'.join(aliases[0].Alias)
    await alias_song.send(msg)


@alias_local_apply.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    if len(args) != 2:
        await alias_local_apply.finish('参数错误')
    id_, alias_name = args
    if not mai.total_list.by_id(id_):
        await alias_local_apply.finish(f'未找到ID为 [{id_}] 的曲目')
    server_exist = await maiApi.get_songs(id_)
    if alias_name in server_exist[id_]:
        await alias_local_apply.finish(f'该曲目的别名 <{alias_name}> 已存在别名服务器，不能重复添加别名，如果bot未生效，请联系BOT管理员使用指令 <更新别名库>')
    local_exist = mai.total_alias_list.by_id(id_)
    if local_exist and alias_name.lower() in local_exist[0].Alias:
        await alias_local_apply.finish(f'本地别名库已存在该别名')
    issave = await update_local_alias(id_, alias_name)
    if not issave:
        msg = '添加本地别名失败'
    else:
        msg = f'已成功为ID <{id_}> 添加别名 <{alias_name}> 到本地别名库'
    await alias_local_apply.send(msg)


@alias_apply.handle()
async def _(event: GroupAtMessageCreateEvent, arg: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        args = arg.extract_plain_text().strip().split()
        if len(args) != 2:
            await alias_apply.finish('参数错误')
        id_, alias_name = args
        if not mai.total_list.by_id(id_):
            await alias_apply.finish(f'未找到ID为 [{id_}] 的曲目')
        isexist = await maiApi.get_songs(id_)
        if alias_name in isexist[id_]:
            await alias_apply.finish(f'该曲目的别名 <{alias_name}> 已存在，不能重复添加别名，如果bot未生效，请联系BOT管理员使用指令 <更新别名库>')
        tag = ''.join(sample(ascii_uppercase + digits, 5))
        status = await maiApi.post_alias(id_, alias_name, tag, user_id)
        if isinstance(status, str):
            await alias_apply.finish(status)
        msg = dedent(f'''\
            您已提交以下别名申请
            ID：{id_}
            别名：{alias_name}
            现在可用使用唯一标签<{tag}>来进行投票，例如：同意别名 {tag}
            ''') + await draw_music_info(mai.total_list.by_id(id_))
    except ServerError as e:
        log.error(e)
        msg = str(e)
    except ValueError as e:
        log.error(traceback.format_exc())
        msg = str(e)
    except UserNotBindError as e:
        await alias_apply.send(str(e))
    await alias_apply.send(msg)


@alias_agree.handle()
async def _(arg: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        tag = arg.extract_plain_text().strip().upper()
        status = await maiApi.post_agree_user(tag, user_id)
        if 'content' in status:
            await alias_agree.finish(status['content'])
        if 'error' in status:
            await alias_agree.finish(status['error'])
        else:
            await alias_agree.finish(str(status))
    except ValueError as e:
        await alias_agree.send(str(e))
    except UserNotBindError as e:
        await alias_agree.send(str(e))


@alias_status.handle()
async def _(event: GroupAtMessageCreateEvent, arg: Message = CommandArg()):
    try:
        args = arg.extract_plain_text().strip()
        status = await maiApi.get_alias_status()
        if not status:
            await alias_status.finish('未查询到正在进行的别名投票')
        page = max(min(int(args), len(status) // SONGS_PER_PAGE + 1), 1) if args else 1
        result = []
        for num, tag in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                result.append(dedent(f'''{tag}：\
                    - ID：{status[tag]['ID']}
                    - 别名：{status[tag]['ApplyAlias']}
                    - 票数：{status[tag]['Users']}/{status[tag]['Votes']}'''))
        result.append(f'第{page}页，共{len(status) // SONGS_PER_PAGE + 1}页')
        msg = MessageSegment.image(await image_to_save(text_to_image('\n'.join(result))))
    except ServerError as e:
        log.error(str(e))
        msg = str(e)
    except ValueError as e:
        msg = str(e)
    await alias_status.send(msg)


@alias_update.handle()
async def _():
    try:
        await mai.get_music_alias()
        log.info('手动更新别名库成功')
        await alias_update.send('手动更新别名库成功')
    except:
        log.error('手动更新别名库失败')
        await alias_update.send('手动更新别名库失败')


@score.handle()
async def _(event: GroupAtMessageCreateEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    argslist = args.split()
    if args and argslist[0] == '帮助':
        msg = dedent('''\
            此功能为查找某首歌分数线设计。
            命令格式：分数线 <难度+歌曲id> <分数线>
            例如：分数线 紫799 100
            命令将返回分数线允许的 TAP GREAT 容错以及 BREAK 50落等价的 TAP GREAT 数。
            以下为 TAP GREAT 的对应表：
            GREAT/GOOD/MISS
            TAP\t1/2.5/5
            HOLD\t2/5/10
            SLIDE\t3/7.5/15
            TOUCH\t1/2.5/5
            BREAK\t5/12.5/25(外加200落)''')
        await score.finish(MessageSegment.image(await image_to_save(text_to_image(msg))))
    else:
        try:
            result = re.search(r'([绿黄红紫白])\s?([0-9]+)', args)
            level_labels = ['绿', '黄', '红', '紫', '白']
            level_index = level_labels.index(result.group(1))
            chart_id = result.group(2)
            line = float(args[-1])
            music = mai.total_list.by_id(chart_id)
            chart = music.charts[level_index]
            tap = int(chart.notes.tap)
            slide = int(chart.notes.slide)
            hold = int(chart.notes.hold)
            touch = int(chart.notes.touch) if len(chart.notes) == 5 else 0
            brk = int(chart.notes.brk)
            total_score = tap * 500 + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            msg = dedent(f'''\
                {music.title} {diffs[level_index]}
                分数线 {line}% 允许的最多 TAP GREAT 数量为 {(total_score * reduce / 10000):.2f}(每个-{10000 / total_score:.4f}%),
                BREAK 50落(一共{brk}个)等价于 {(break_50_reduce / 100):.3f} 个 TAP GREAT(-{break_50_reduce / total_score * 100:.4f}%)''')
            await score.finish(MessageSegment.image(await image_to_save(text_to_image(msg))))
        except (AttributeError, ValueError) as e:
            log.exception(e)
            await score.finish('格式错误，输入“分数线 帮助”以查看帮助信息')


@best50.handle()
async def _(arg: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    username = arg.extract_plain_text().split()
    try:
        await best50.finish(await generate(user_id, username))
    except UserNotBindError as e:
        await best50.send(str(e))


@minfo.handle()
async def _(event: GroupAtMessageCreateEvent, arg: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        args = arg.extract_plain_text().strip()
        if not args:
            await minfo.finish('请输入曲目id或曲名')

        if mai.total_list.by_id(args):
            songs = args
        elif by_t := mai.total_list.by_title(args):
            songs = by_t.id
        else:
            aliases = mai.total_alias_list.by_alias(args)
            if not aliases:
                await minfo.finish('未找到曲目')
            elif len(aliases) != 1:
                msg = '找到相同别名的曲目，请使用以下ID查询：\n'
                for songs in aliases:
                    msg += f'{songs.ID}：{songs.Name}\n'
                await minfo.finish(msg.strip())
            else:
                songs = str(aliases[0].ID)

        if maiApi.token:
            pic = await music_play_data_dev(user_id, songs)
        else:
            pic = await music_play_data(user_id, songs)

        await minfo.finish(pic)
    except UserNotBindError as e:
        await minfo.send(str(e))


@ginfo.handle()
async def _(event: GroupAtMessageCreateEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if not args:
        await ginfo.finish('请输入曲目id或曲名')
    if args[0] not in '绿黄红紫白':
        level_index = 3
    else:
        level_index = '绿黄红紫白'.index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish('请输入曲目id或曲名')
    if mai.total_list.by_id(args):
        id = args
    elif by_t := mai.total_list.by_title(args):
        id = by_t.id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            await ginfo.finish('未找到曲目')
        elif len(alias) != 1:
            msg = '找到相同别名的曲目，请使用以下ID查询：\n'
            for songs in alias:
                msg += f'{songs.ID}：{songs.Name}\n'
            await ginfo.finish(msg.strip())
        else:
            id = str(alias[0].ID)
    music = mai.total_list.by_id(id)
    if not music.stats:
        await ginfo.finish('该乐曲还没有统计信息')
    if len(music.ds) == 4 and level_index == 4:
        await ginfo.finish('该乐曲没有这个等级')
    if not music.stats[level_index]:
        await ginfo.finish('该等级没有统计信息')
    stats = music.stats[level_index]
    pic = await music_global_data(music, level_index)
    await ginfo.finish(pic + dedent(f'''\
        游玩次数：{round(stats.cnt)}
        拟合难度：{stats.fit_diff:.2f}
        平均达成率：{stats.avg:.2f}%
        平均 DX 分数：{stats.avg_dx:.1f}
        谱面成绩标准差：{stats.std_dev:.2f}
        '''))


@table_update.handle()
async def _():
    await table_update.send(await update_rating_table())


@rating_table.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg()):
    args = args.extract_plain_text().strip()
    if args in levelList[:5]:
        await rating_table.send('只支持查询lv6-15的定数表')
    elif args in levelList[5:]:
        if args in levelList[-3:]:
            img = '14'
            # img = ratingdir / '14.png'
        else:
            img = args
            # img = ratingdir / f'{args}.png'
        url = FileServer + f'/rating/{img}.png'
        await rating_table.send(MessageSegment.image(url))
    else:
        await rating_table.send('无法识别的定数')


@rating_table_pf.handle()
async def _(event: GroupAtMessageCreateEvent, args: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        args: str = args.extract_plain_text().strip()
        if args in levelList[:5]:
            await rating_table_pf.send('只支持查询lv6-15的完成表')
        elif args in levelList[5:]:
            pic = await rating_table_draw(user_id, args)
            await rating_table_pf.send(pic)
    # else:
    #     await rating_table_pf.send('无法识别的定数')
    except UserNotBindError as e:
        await rating_table_pf.send(str(e))


@rise_score.handle()  # 慎用，垃圾代码非常吃机器性能
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        username = None
        
        args = message.extract_plain_text().lower()
        match = re.search(r'([0-9]+\+?)?上([0-9]+)分', args)
        
        rating = match.group(1)
        score = match.group(2)
        
        if rating and rating not in levelList:
            await rise_score.finish('无此等级')
        elif match.group(2):
            username = match.group(2).strip()

        data = await rise_score_data(user_id, username, rating, score)
        await rise_score.finish(data)
    except UserNotBindError as e:
        await rise_score.send(str(e))


@plate_process.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        username = None
        
        args = message.extract_plain_text().lower()
        match = re.search(r'^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉熊華华爽舞霸星宙祭祝])([極极将舞神者]舞?)$', args)
        if not match:
            return
        
        ver = match.group(1)
        plan = match.group(2)
        if f'{ver}{plan}' == '真将':
            await plate_process.finish('真系没有真将哦')

        data = await player_plate_data(user_id, username, ver, plan)
        await plate_process.finish(data)
    except UserNotBindError as e:
        await plate_process.send(str(e))


@level_process.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        username = None
        
        args = message.extract_plain_text().lower()
        match = re.search(r'([0-9]+\+?)\s?(.+)', args)
        if not match:
            return
        rating = match.group(1)
        rank = match.group(2)
        
        if rating not in levelList:
            await level_process.finish('无此等级')
        if rank.lower() not in scoreRank + comboRank + syncRank:
            await level_process.finish('无此评价等级')
        if levelList.index(rating) < 11 or (rank.lower() in scoreRank and scoreRank.index(rank.lower()) < 8):
            await level_process.finish('兄啊，有点志向好不好')

        data = await level_process_data(user_id, username, rating, rank)
        await level_process.finish(data)
    except UserNotBindError as e:
        await level_process.send(str(e))


@level_achievement_list.handle()
async def _(event: GroupAtMessageCreateEvent, message: Message = CommandArg(), user_id: int = Depends(get_qqid)):
    try:
        username = None
        
        args = message.extract_plain_text().lower()
        match = re.search(r'([0-9]+\+?)\s?([0-9]+)?', args)
        if not match:
            return
        rating = match.group(1)
        page = match.group(2)
        
        if rating not in levelList:
            await level_achievement_list.finish('无此等级')

        data = await level_achievement_list_data(user_id, username, rating, page)
        await level_achievement_list.send(data)
    except UserNotBindError as e:
        await level_achievement_list.send(str(e))


@rating_ranking.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    page = 1
    name = ''
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()

    data = await rating_ranking_data(name, page)
    await rating_ranking.send(data)


async def data_update_daily():
    await mai.get_music()
    log.info('maimaiDX数据更新完毕')


scheduler.add_job(data_update_daily, 'cron', hour=4)