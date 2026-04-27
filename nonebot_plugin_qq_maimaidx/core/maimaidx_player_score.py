import random
import time
import traceback
from collections import defaultdict
from typing import Callable, DefaultDict, Tuple

import pyecharts.options as opts
from nonebot.adapters.qq import MessageSegment
from PIL import Image
from pyecharts.charts import Pie

from ..config import *
from .image import *
from .maimaidx_api_data import *
from .maimaidx_best_50 import (
    ScoreBaseImage,
    change_column_width,
    coloum_width,
    computeRa,
)
from .maimaidx_model import PlanInfo, PlayInfoDefault, PlayInfoDev, RaMusic
from .maimaidx_music import Music, mai
from .tool import run_chrome_to_base64

Filter = Tuple[
    List[PlayInfoDefault],
    List[PlayInfoDefault],
    List[PlayInfoDefault],
    List[PlayInfoDefault],
    List[PlayInfoDefault]
]
Condition = Callable[[PlayInfoDefault], bool]


def plate_message(
    result: str, 
    plan: str, 
    music_list: List[PlayInfoDefault], 
    played: List[Tuple[int, int]]
) -> Union[MessageSegment, str]:
    """
    Params:
        `result`: 结果
        `plan`: 目标
        `music_list`: 谱面列表
        `played`: 已游玩谱面
    Returns:
        `Union[MessageSegment, str]`
    """
    for n, m in enumerate(music_list):
        self_record = ''
        if (m.song_id, m.difficulties.level_index) in played:
            if plan in ['将', '者']:
                self_record = f'{m.achievements}%'
            if plan in ['極', '极', '神']:
                self_record = m.fc
            if plan in '舞舞':
                self_record = m.fs
        result += f'No.{n + 1:02d} {f"「{m.song_id}」":>7} {f"「{DIFFS[m.difficulties.level_index]}」":>11} 「{m.ds}」 {m.title}  {self_record}\n'
    if len(music_list) > 10:
        result = MessageSegment.file_image(image_to_bytesio(text_to_image(result.strip())))
    return result


async def player_plate_data(
    qqid: int, 
    username: str, 
    version: str, 
    plan: str
) -> Union[MessageSegment, str]:
    """
    查看牌子进度
    
    Params:
        `qqid`: 用户QQ
        `username`: 查分器用户名
        `ver`: 版本
        `plan`: 目标
    Returns:
        `Union[MessageSegment, str]`
    """
    if version in PLATE_CN:
        version = PLATE_CN[version]
    ver, _ver = VERSION_MAP.get(version, ([DX_VERSION.get(version)], version))
    
    try:
        verlist = await maiApi.query_user_plate(qqid=qqid, username=username, version=ver)
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        return str(e)
    
    if plan in ['将', '者']:
        achievement = 100 if plan == '将' else 80
        callable_: Condition = lambda x: x.achievements < achievement
    elif plan in ['極', '极']:
        callable_: Condition = lambda x: not x.fc
    elif plan == '舞舞':
        callable_: Condition = lambda x: x.fs not in ['fsd', 'fsdp']
    elif plan  == '神':
        callable_: Condition = lambda x: x.fc not in ['ap', 'app']
    else:
        raise ValueError
    
    unfinished_model_list: Filter = ([], [], [], [], [])
    unfinished: List[Tuple[int, int]] = []
    played: List[Tuple[int, int]] = []
    remaster: List[int] = []
    
    # 已游玩未完成曲目
    plate_id_list = mai.total_plate_id_list[_ver]
    if _ver in ['舞', '霸']:
        remaster = mai.total_plate_id_list['舞ReMASTER']
        for music in verlist:
            if music.song_id not in plate_id_list:
                continue
            if music.difficulties.level_index == 4 and music.song_id not in remaster:
                continue
            if callable_(music):
                unfinished.append((music.song_id, music.difficulties.level_index))
            played.append((music.song_id, music.difficulties.level_index))
    else:
        for music in verlist:
            if music.song_id not in plate_id_list:
                continue
            if callable_(music):
                unfinished.append((music.song_id, music.difficulties.level_index))
            played.append((music.song_id, music.difficulties.level_index))
    
    # 未游玩未完成曲目
    for music in mai.total_list:
        if int(music.id) not in plate_id_list:
            continue
        info = PlayInfoDefault(
            achievements=0,
            level='',
            level_index=0,
            title=music.title,
            type=music.type,
            id=int(music.id)
        )
        range_ = range(5 if version in ['舞', '霸'] and int(music.id) in remaster else 4)
        for level_index in range_:
            if (m := (info.song_id, level_index)) not in played or m in unfinished:
                _info = info.model_copy()
                _info.level = music.level[level_index]
                _info.ds = music.ds[level_index]
                _info.difficulties.level_index = level_index
                unfinished_model_list[level_index].append(_info)

    basic, advanced, expert, master, re_master = unfinished_model_list
    
    ramain = basic + advanced + expert + master + re_master
    ramain.sort(key=lambda x: x.ds, reverse=True)
    difficult = [_m for _m in ramain if _m.ds > 13.6]

    appellation = username if username else '您'
    result = dedent(f'''\
        {appellation}的「{version}{plan}」剩余进度如下：
        Basic剩余「{len(basic)}」首
        Advanced剩余「{len(advanced)}」首
        Expert剩余「{len(expert)}」首
        Master剩余「{len(master)}」首
    ''')
    if version in ['舞', '霸']:
        result += f'Re:Master剩余「{len(re_master)}」首\n'
    
    if len(difficult) > 0:
        if len(difficult) < 60:
            result += '剩余定数大于13.6的曲目：\n'
            result = plate_message(result, plan, difficult, played)
        else:
            result += f'还有{len(difficult)}首大于13.6定数的曲目，加油推分捏！\n'
    elif len(ramain) > 0:
        if len(ramain) < 60:
            result += '剩余曲目：\n'
            result = plate_message(result, plan, ramain, played)
        else:
            result += '已经没有定数大于13.6的曲目了，加油清谱捏！\n'
    else:
        result = f'已经没有剩余的的曲目了，恭喜{appellation}完成「{version}{plan}」！'
    return result


async def rating_ranking_data(name: str, page: int) -> Union[MessageSegment, str]:
    """
    查看查分器排行榜
    
    Params:
        `name`: 指定用户名
        `page`: 页数
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        rank_data = await maiApi.rating_ranking()

        _time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if name != '':
            if name in [r.username.lower() for r in rank_data]:
                rank_index = [r.username.lower() for r in rank_data].index(name) + 1
                nickname = rank_data[rank_index - 1].username
                data = f'截止至 {_time}\n玩家 {nickname} 在查分器已注册用户ra排行第{rank_index}'
            else:
                data = '未找到该玩家'
        else:
            user_num = len(rank_data)
            msg = f'截止至 {_time}，查分器已注册用户ra排行：\n'
            if page * 50 > user_num:
                page = user_num // 50 + 1
            end = page * 50 if page * 50 < user_num else user_num
            for i, ranker in enumerate(rank_data[(page - 1) * 50:end]):
                msg += f'No.{i + 1 + (page - 1) * 50:02d}.「{ranker.ra}」 {ranker.username} \n'
            msg += f'第「{page}」页，共「{user_num // 50 + 1}」页'
            data = MessageSegment.file_image(text_to_bytes_io(msg.strip()))
    except Exception as e:
        log.error(traceback.format_exc())
        data = f'未知错误：{type(e)}\n请联系Bot管理员'
    return data