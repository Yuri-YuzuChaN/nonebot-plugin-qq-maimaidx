from nonebot.adapters.qq.message import LocalAttachment, MessageSegment

from ..config import dfconfig
from ..constants import *
from .clients.divingfish.client import DivingFishAPI
from .clients.exceptions import *
from .clients.lxns.client import LxnsAPI, OAuth2
from .clients.lxns.models.enum import SongType
from .clients.lxns.models.oauth import *
from .database.qq import User, update_user
from .image.best50 import PlayerBest50
from .image.chart import song_chart_info, song_global_data
from .image.info import song_play_data
from .image.score import DrawScore
from .image.table import DrawPlateTable, DrawRatingTable
from .image.tools import tricolor_gradient_prism_plus
from .merge.models.category import Category
from .merge.models.score import NotPlayedResult, PlayedResult
from .merge.models.service import ServiceName
from .merge.models.song import Song
from .merge.models.theme import Theme
from .merge.play_result import df_to_playresult, lxns_to_playresult
from .merge.player import df_to_best50, df_to_player, lxns_to_best50
from .service import mai
from .utils.song_id import get_charts_id

PLAN_MAP: dict[str, tuple[int, int | float]] = {
    **{p: (0, ACHIEVEMENT_LIST[i-1]) for i, p in enumerate(RANK_PLUS)},
    **{p: (1, i) for i, p in enumerate(COMBO_PLUS)},
    **{p: (2, i) for i, p in enumerate(SYNC_PLUS)}
}


def get_token(user: User) -> BaseToken:
    return BaseToken(
        access_token=user.access_token, 
        refresh_token=user.refresh_token
    )


async def get_friend_code(
    qqid: int,
    token: OAuth2Token | BaseToken, 
) -> int:
    api = LxnsAPI(qqid, token=token)
    player = await api.player()
    return player.friend_code


async def bind_lxns(user: User, code: str) -> str:
    oauth = OAuth2()
    token = await oauth.fetch_token(code)
    friend_code = await get_friend_code(user.qqid, token)
    update = await update_user(user.open_id, friend_code=friend_code, token=token)
    if update is None:
        result = "数据库错误。"
    else:
        result = "授权完成。"
    return result


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
            data = await api.query_user_plate(version=ALL_VERSION, song_id=song.song_id)
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


async def draw_chart_info(song: Song, user: User | None = None) -> LocalAttachment:
    """
    绘制谱面信息
    
    Params:
        `song`: 曲目
        `user`: 用户 `User` 模型
    Returns:
        `LocalAttachment`
    """
    calc = False
    is_full = False
    best_list = []
    if user is not None:
        theme = user.theme
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
    else:
        theme = Theme.CIRCLE
        
    image = song_chart_info(song, calc, is_full, best_list, theme)
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
    level: str, 
    plan: str, 
    category: Category, 
    page: int = 1
) -> LocalAttachment:
    """
    绘制谱面等级进度

    Params:
        `user`: 用户 `User` 模型
        `level`: 定数
        `plan`: 评价等级
    Returns:
        `LocalAttachment`
    """
    play_result = await get_player_result(user, ALL_VERSION)
    played_map: dict[tuple[int, int], PlayedResult] = {
        (r.song_id, r.level_index): r for r in play_result if r.level == level
    }
    plan_type, plan_value = PLAN_MAP[plan]
    
    def check_status(res: PlayedResult) -> bool:
        if plan_type == 0:  # Achievement
            return res.achievements >= plan_value
        if plan_type == 1:  # Combo
            return bool(res.fc and COMBO_SP.index(res.fc) >= plan_value)
        if plan_type == 2:  # Sync
            if not res.fs: return False
            sync_list = SYNC_D_SP if res.fs in SYNC_D_SP else SYNC_SP
            return sync_list.index(res.fs) >= plan_value
        return False

    completed: list[PlayedResult] = []
    unfinished: list[PlayedResult] = []
    notplayed: list[NotPlayedResult] = []
    
    music_list = mai.total_list.by_plan(level)
    for song_id, difficulties in music_list.items():
        for _d in difficulties:
            res = played_map.get((song_id, _d.level_index))
            if res:
                if check_status(res):
                    completed.append(res)
                else:
                    unfinished.append(res)
            else:
                notplayed.append(
                    NotPlayedResult(
                        level_value=_d.level_value,
                        song_id=song_id,
                        level_index=_d.level_index
                    )
                )
    
    sort_key = {0: "achievements", 1: "fc", 2: "fs"}.get(plan_type, "achievements")
    completed.sort(key=lambda x: getattr(x, sort_key), reverse=True)
    unfinished.sort(key=lambda x: getattr(x, sort_key), reverse=True)
    notplayed.sort(key=lambda x: x.level_value, reverse=True)
    
    if category == Category.DEFAULT:
        comp_limit = 60 if not unfinished and not notplayed else 30
        c_y = (len(completed[:comp_limit]) // 5 + 1) * 109 + 140
        u_y = (len(unfinished[:30]) // 5 + 1) * 109 + 140
        n_y = (len(notplayed[:100]) // 20 + 1) * 65 + 140
        
        background_bg = tricolor_gradient_prism_plus(1400, 150 + c_y + u_y + n_y)
        ds = DrawScore(user.service, background_bg)
        image = ds.draw_plan(completed, c_y, unfinished, u_y, notplayed, plan, comp_limit)
    elif category in [Category.COMPLETED, Category.UNFINISHED]:
        data = completed if category == Category.COMPLETED else unfinished
        per_page = 80
        total_page = (len(data) - 1) // per_page + 1
        if page > total_page:
            page = total_page
        
        display_data = data[(page - 1) * per_page : page * per_page]
        y_size = (len(display_data) // 5 + 1) * 109
        background_bg = tricolor_gradient_prism_plus(1400, 240 + y_size + 120)
        ds = DrawScore(user.service, background_bg)
        image = ds.draw_category(category, data, page, total_page)
    
    else:
        y_size = (len(notplayed) // 20 + 1) * 65
        background_bg = tricolor_gradient_prism_plus(1400, 240 + y_size + 120)
        ds = DrawScore(user.service, background_bg)
        image = ds.draw_category(category, notplayed)
    
    return MessageSegment.file_image(image)


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
    play_result = await get_player_result(user, ALL_VERSION)
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
    