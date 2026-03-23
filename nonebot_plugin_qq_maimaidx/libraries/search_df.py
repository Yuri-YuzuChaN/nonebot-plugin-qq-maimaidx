import traceback

from nonebot.adapters.qq.message import LocalAttachment, MessageSegment

from ..config import DX_VERSION, PLATE_CN, VERSION_MAP, dfconfig, log
from .clients.divingfish.client import DivingFishAPI
from .clients.exceptions import *
from .domain.models.service import ServiceName
from .domain.models.song import Song
from .domain.play_result import df_to_playresult
from .domain.player import df_to_best50, df_to_player
from .image.best50 import PlayerBest50
from .image.chart import song_chart_info
from .image.info import song_play_data
from .image.table import DrawPlateTable, DrawRatingTable


async def draw_df_best50(
    qqid: int | None = None, 
    username: str | None = None,
    icon: str | None = None
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
        api = DivingFishAPI(qqid, username)
        userinfo = await api.query_user_b50()
        b50 = PlayerBest50(
            ServiceName.DIVINGFISH, 
            player=df_to_player(userinfo),
            best50=df_to_best50(userinfo),
            qqid=qqid,
            icon=icon
        )
        
        msg = MessageSegment.file_image(await b50.draw())
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f"未知错误：{type(e)}\n请联系Bot管理员"
    return msg


async def draw_df_play_data(qqid: int, song: Song) -> LocalAttachment:
    """
    绘制单曲游玩成绩
    """
    api = DivingFishAPI(qqid=qqid)
    if dfconfig.divingfish_token:
        data = await api.query_user_post_dev(song_id=song.song_id)
        isdev = True
    else:
        version = list(set(_v for _v in DX_VERSION.values()))
        data = await api.query_user_plate(version=version, song_id=song.song_id)
        isdev = False
    
    if not data:
        raise MusicNotPlayError
    
    play_result = df_to_playresult(data, song=song)
    image = song_play_data(
        ServiceName.DIVINGFISH, 
        song=song, 
        play_result=play_result, 
        isdev=isdev
    )
    return MessageSegment.file_image(image)


async def draw_df_chart_info(song: Song, *, qqid: int | None = None) -> LocalAttachment:
    """
    绘制谱面信息
    """
    calc = True
    is_full = True
    best_list = []
    api = DivingFishAPI(qqid=qqid)
    try:
        if qqid:
            userinfo = await api.query_user_b50()
            best50 = df_to_best50(userinfo)
            if song.isnew:
                best_list = best50.dx
                is_full = bool(len(best_list) == 15)
            else:
                best_list = best50.sd
                is_full = bool(len(best_list) == 35)
        else:
            calc = False
    except Exception:
        calc = False
    
    image = song_chart_info(song, calc, is_full, best_list)
    return MessageSegment.file_image(image)


async def draw_df_rating_table(qqid: int, rating: str, is_fc: bool) -> LocalAttachment:
    """
    绘制定数表
    """
    api = DivingFishAPI(qqid=qqid)
    version = list(set(_v for _v in DX_VERSION.values()))
    data = await api.query_user_plate(version=version)
    play_result = df_to_playresult(data)
    
    table = DrawRatingTable(ServiceName.DIVINGFISH, play_result, rating=rating, is_fc=is_fc)
    image = table.draw()
    return MessageSegment.file_image(image)


async def draw_df_plate_table(qqid: int, version: str, plan: str) -> LocalAttachment:
    """
    绘制完成表
    """
    if version in PLATE_CN:
        version = PLATE_CN[version]
    ver, version_name = VERSION_MAP.get(version, ([DX_VERSION[version]], version))
    api = DivingFishAPI(qqid=qqid)
    data = await api.query_user_plate(version=ver)
    play_result = df_to_playresult(data)
    
    table = DrawPlateTable(
        ServiceName.DIVINGFISH, 
        play_result, 
        plan=plan, 
        version_name=version_name
    )
    image = table.draw()
    return MessageSegment.file_image(image)