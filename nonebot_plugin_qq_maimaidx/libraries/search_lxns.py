import traceback

from nonebot.adapters.qq.message import LocalAttachment, MessageSegment

from ..config import log
from ..constants import DX_VERSION
from .clients.exceptions import *
from .clients.lxns.client import LxnsAPI
from .clients.lxns.models.enum import SongType
from .clients.lxns.models.oauth import *
from .image.best50 import PlayerBest50
from .image.chart import song_chart_info
from .image.info import song_play_data
from .image.table import DrawPlateTable, DrawRatingTable
from .merge.models.score import PlayResult
from .merge.models.service import ServiceName
from .merge.models.song import Song
from .merge.play_result import lxns_to_playresult
from .merge.player import lxns_to_best50
from .service import mai


async def draw_lxns_best50(
    qqid: int | None = None, 
    token: BaseToken | None = None, 
    *, 
    all_perfect: bool = False
) -> LocalAttachment | str:
    """
    生成b50
    
    Params:
        `qqid`: QQ号
        `username`: 用户名
        `icon`: 头像
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        api = LxnsAPI(qqid, token)
        player = await api.player()
        if all_perfect:
            b50 = await api.ap50(player.friend_code)
        else:
            b50 = await api.best50()
        best50 = lxns_to_best50(b50)
        
        pb50 = PlayerBest50(ServiceName.LXNS, player=player, best50=best50)
        
        msg = MessageSegment.file_image(await pb50.draw())
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f"未知错误：{type(e)}\n请联系Bot管理员"
    return msg


async def draw_lxns_play_data(song: Song, token: BaseToken) -> LocalAttachment:
    api = LxnsAPI(token=token)
    if song.song_id < 10000:
        song_type = SongType.STANDARD
    elif song.song_id < 100000:
        song_type = SongType.DX
    else:
        song_type = SongType.UTAGE
    
    data = await api.all_best(song.song_id, song_type)
    if not data:
        raise MusicNotPlayError
    
    play_result = lxns_to_playresult(song, data)
    image = song_play_data(ServiceName.LXNS, song=song, play_result=play_result)
    return MessageSegment.file_image(image)


async def draw_df_chart_info(song_id: int, token: BaseToken | None = None) -> LocalAttachment:
    calc = True
    isfull = True
    bestlist = []
    song = mai.total_list.by_id(song_id)
    api = LxnsAPI(token=token)
    try:
        if token:
            best50 = lxns_to_best50(await api.best50())
            if song.version_str == list(DX_VERSION.values())[-1]:
                bestlist = best50.dx
                isfull = bool(len(bestlist) == 15)
            else:
                bestlist = best50.sd
                isfull = bool(len(bestlist) == 35)
        else:
            calc = False
    except Exception:
        calc = False
    
    image = song_chart_info(song, calc, isfull, bestlist)
    return MessageSegment.file_image(image)


async def draw_rating_table(
    rating: str, 
    play_result: list[PlayResult], 
    *, 
    if_fc: bool = False
) -> LocalAttachment:
    table = DrawRatingTable(
        rating, 
        service=ServiceName.LXNS, 
        play_result=play_result,
        is_fc=if_fc
    )
    image = table.draw()
    
    return MessageSegment.file_image(image)