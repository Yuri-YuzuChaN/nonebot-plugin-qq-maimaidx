from nonebot.adapters.qq.message import LocalAttachment, MessageSegment

from ..config import dfconfig
from ..constants import DX_VERSION, VERSION_MAP
from .clients.divingfish.client import DivingFishAPI
from .clients.exceptions import *
from .clients.lxns.client import LxnsAPI
from .clients.lxns.models.enum import SongType
from .clients.lxns.models.oauth import *
from .database.qq import User
from .image.best50 import PlayerBest50
from .image.chart import song_chart_info, song_global_data
from .image.info import song_play_data
from .image.score import DrawScore
from .image.table import DrawPlateTable, DrawRatingTable
from .image.tools import tricolor_gradient_prism_plus
from .merge.models.score import PlayedResult
from .merge.models.service import ServiceName
from .merge.models.song import Song
from .merge.play_result import df_to_playresult, lxns_to_playresult
from .merge.player import df_to_best50, df_to_player, lxns_to_best50
from .service import mai
from .utils.song_id import get_charts_id


def get_token(user: User) -> BaseToken:
    return BaseToken(
        access_token=user.access_token, 
        refresh_token=user.refresh_token
    )


async def get_player_result(
    user: User, 
    vesrion: list[str] | None = None
) -> list[PlayedResult]:
    """
    获取游玩成绩
    
    Params:
        `service`: 数据源
        `user`: 用户 `User` 模型
        `token`: OAuth2 Token（仅LXNS）
        `version`: 版本列表（仅DivingFish）
    Returns:
        `list[PlayedResult]`
    """
    if user.service == ServiceName.DIVINGFISH:
        api = DivingFishAPI(qqid=user.qqid)
        if dfconfig.divingfish_token:
            result = await api.query_user_get_dev()
            data = result.records
        else:
            data = await api.query_user_plate(version=vesrion)
        play_result = df_to_playresult(data)
    elif user.service == ServiceName.LXNS:
        token = get_token(user)
        api = LxnsAPI(user.open_id, token)
        data = await api.all_best()
        play_result = lxns_to_playresult(data)
    else:
        raise ValueError
    return play_result


async def draw_song_galobal_data(
    song_id: int, 
    level_index: int
) -> LocalAttachment:
    """
    绘制谱面数据
    
    Params:
        `song_id`: 曲目ID
        `level_index`: 等级索引
    Returns:
        `LocalAttachment`
    """
    song = mai.total_list.by_id(song_id)
    image = await song_global_data(song, level_index)
    return MessageSegment.file_image(image)


def draw_rating_table_text(rating: str) -> LocalAttachment:
    """
    绘制只有等级文本的定数表
    
    Params:
        `rating`: 定数
    Returns:
        `LocalAttachment`
    """
    table = DrawRatingTable(rating, level_text=True)
    image = table.draw()
    return MessageSegment.file_image(image)


async def draw_best50(
    user: User,
    *,
    username: str | None = None,
    icon: str | None = None,
    all_perfect: bool = False
) -> LocalAttachment:
    """
    绘制best50
    
    Params:
        `service`: 数据源
        `user`: 用户 `User` 模型
        `username`: 用户名
        `icon`: 头像
        `token`: OAuth2 Token（仅LXNS）
        `all_perfect`: 绘制AP（仅LXNS）
    Returns:
        `LocalAttachment`
    """
    if user.service == ServiceName.DIVINGFISH:
        api = DivingFishAPI(user.qqid, username)
        userinfo = await api.query_user_b50()
        b50 = PlayerBest50(
            user.service,
            user.theme,
            player=df_to_player(userinfo),
            best50=df_to_best50(userinfo),
            qqid=user.qqid,
            icon=icon
        )
    elif user.service == ServiceName.LXNS:
        token = get_token(user)
        api = LxnsAPI(user.open_id, token)
        player = await api.player()
        if all_perfect:
            obj = await api.ap50(player.friend_code)
        else:
            obj = await api.best50()
        best50 = lxns_to_best50(obj)
        
        b50 = PlayerBest50(user.service, user.theme, player=player, best50=best50)
    else:
        raise ValueError
    
    return MessageSegment.file_image(await b50.draw())


async def draw_play_data(
    user: User,
    song: Song,
    service: ServiceName | None = None
) -> LocalAttachment:
    """
    绘制单曲游玩成绩
    
    Params:
        `service`: 数据源
        `song`: 曲目
        `user`: 用户 `User` 模型
        `token`: OAuth2 Token（仅LXNS）
    Returns:
        `LocalAttachment`
    """
    isdev = False
    if service is None:
        service = user.service
    if service == ServiceName.DIVINGFISH:
        api = DivingFishAPI(qqid=user.qqid)
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
    elif service == ServiceName.LXNS:
        token = get_token(user)
        api = LxnsAPI(user.open_id, token)
        if song.song_id < 10000:
            song_type = SongType.STANDARD
        elif song.song_id < 100000:
            song_type = SongType.DX
        else:
            song_type = SongType.UTAGE
        song_id = get_charts_id(song.song_id)
        
        data = await api.song_bests(song_id, song_type)
        if not data:
            raise MusicNotPlayError
        
        play_result = lxns_to_playresult(data, song=song)
    else:
        raise ValueError
    
    image = song_play_data(
        user.service, 
        user.theme, 
        song=song, 
        play_result=play_result, 
        isdev=isdev
    )
    return MessageSegment.file_image(image)


async def draw_chart_info(song: Song, user: User) -> LocalAttachment:
    """
    绘制谱面信息
    
    Params:
        `service`: 数据源
        `song`: 曲目
        `user`: 用户 `User` 模型
        `token`: OAuth2 Token（仅LXNS）
    Returns:
        `LocalAttachment`
    """
    calc = False
    is_full = False
    best_list = []
    try:
        if user.service == ServiceName.DIVINGFISH:
            api = DivingFishAPI(qqid=user.qqid)
            userinfo = await api.query_user_b50()
            best50 = df_to_best50(userinfo)
            calc = True
        elif user.service == ServiceName.LXNS:
            token = get_token(user)
            api = LxnsAPI(user.open_id, token)
            best50 = lxns_to_best50(await api.best50())
            calc = True
        else:
            raise ValueError
        
        if calc:
            if song.isnew:
                best_list = best50.dx
                is_full = bool(len(best_list) == 15)
            else:
                best_list = best50.sd
                is_full = bool(len(best_list) == 35)      
    except Exception:
        calc = False
        
    image = song_chart_info(song, calc, is_full, best_list, user.theme)
    return MessageSegment.file_image(image)


async def draw_rating_table(
    user: User, 
    rating: str, 
    plan: bool = False
) -> LocalAttachment:
    """
    绘制定数表
    
    Params:
        `service`: 数据源
        `rating`: 定数
        `user`: 用户 `User` 模型
        `plan`: 指定计划
    Returns:
        `LocalAttachment`
    """
    play_result = await get_player_result(user)
    table = DrawRatingTable(
        rating, 
        service=user.service, 
        play_result=play_result,
        plan=plan
    )
    image = table.draw()    
    return MessageSegment.file_image(image)


async def draw_plate_table(
    user: User, 
    version: str,
    plan: str,
    page: int,
) -> LocalAttachment:
    """
    绘制完成表
    
    Params:
        `service`: 数据源
        `version`: 版本
        `plan`: 指定计划
        `user`: 用户 `User` 模型
        `page`: 页数
        `token`: OAuth2 Token（仅LXNS）
    Returns:
        `LocalAttachment`
    """
    _version, version_name = VERSION_MAP.get(version)
    play_result = await get_player_result(user, _version)
    table = DrawPlateTable(
        user.service,
        play_result, 
        plan=plan, 
        version=version, 
        version_name=version_name,
        page=page
    )
    image = table.draw()
    return MessageSegment.file_image(image)


async def draw_plate_progress() -> LocalAttachment:
    """
    绘制牌子完成进度

    Params:
        `service`: 数据源
        `user`: 用户 `User` 模型
        `level`: 定数
        `plan`: 评价等级
        `token`: OAuth2 Token（仅LXNS）
    Returns:
        `LocalAttachment`
    """


async def draw_level_progress(
    user: User,
    page: int = 1
) -> LocalAttachment:
    """
    绘制谱面等级进度

    Params:
        `service`: 数据源
        `user`: 用户 `User` 模型
        `level`: 定数
        `plan`: 评价等级
        `token`: OAuth2 Token（仅LXNS）
    Returns:
        `LocalAttachment`
    """


async def draw_level_score_list(
    user: User,
    rating: str | float,
    page: int = 1,
) -> LocalAttachment:
    """
    绘制分数列表

    Params:
        `rating`: 等级或定数
        `user`: 用户 `User` 模型
        `page`: 页数
    Returns:
        `LocalAttachment`
    """
    version = list(set(_v for _v in DX_VERSION.values()))
    play_result = await get_player_result(user, version)
    new_play_result = sorted(
        filter(
            (lambda x: x.level == rating) 
            if isinstance(rating, str) else 
            (lambda x: x.level_value == rating),
            play_result
        ), 
        key=lambda y: y.achievements, reverse=True
    )
    
    result_sum = len(new_play_result)
    end_page = (result_sum + 79) // 80
    if page > end_page:
        page = end_page
    
    to_page = 80 if page < end_page else (result_sum % 80 or 80)
    line = (to_page + 4) // 5
    if page < end_page:
        plc = line * 109 + 140 * 4
    else:
        multiplier = (to_page + 19) // 20
        actual_line = 4 if to_page <= 20 else line
        plc = actual_line * 109 + 140 * multiplier
    
    background_bg = tricolor_gradient_prism_plus(1400, 210 + plc)
    
    score = DrawScore(background_bg, user.theme)
    image = score.draw_score_list(rating, new_play_result, page, end_page)
    return MessageSegment.file_image(image)


async def draw_rise_score_list() -> LocalAttachment:
    """
    绘制上分推荐表
    """


async def draw_rating_ranking() -> LocalAttachment:
    """
    查看查分器排行榜
    """
    