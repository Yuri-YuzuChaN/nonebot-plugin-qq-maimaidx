from ..clients.divingfish.models.score import PlayInfoDefault, PlayInfoDev
from ..clients.lxns.models.enum import SongType
from ..clients.lxns.models.score import Score
from ..utils.calc import calc_ds
from .models.score import PlayNotResult, PlayResult
from .models.song import Song


def format_result(
    v: PlayInfoDefault | PlayInfoDev, 
    level_value: float = 0
) -> PlayResult:
    return PlayResult(
        song_id=v.song_id, 
        song_name=v.title, 
        level=v.level, 
        level_index=v.level_index, 
        level_value=level_value,
        type=v.type, 
        rating=v.ra, 
        achievements=v.achievements, 
        fc=v.fc, 
        fs=v.fs, 
        rate=v.rate, 
        dx_score=v.dxScore
    )


def df_to_playresult(
    data: list[PlayInfoDefault] | list[PlayInfoDev],
    *, 
    song: Song | None = None
) -> list[PlayResult | PlayNotResult]:
    if song:
        r = [PlayNotResult(level_value=v.level_value) for v in song.difficulties]
    else:
        r = []
    
    for v in data:
        if song:
            r[v.level_index] = format_result(v, r[v.level_index].level_value)
        else:
            r.append(format_result(v))
            
    return r


def lxns_to_playresult(song: Song, data: list[Score]) -> list[PlayResult | PlayNotResult]:
    r = [PlayNotResult(level_value=v.level_value) for v in song.difficulties]
    for v in data:
        r[v.level_index] = PlayResult(
            song_id=v.id if v.type == SongType.STANDARD else v.id + 10000,
            song_name=v.song_name,
            level=v.level,
            level_index=v.level_index,
            type=v.type,
            rating=v.dx_rating,
            achievements=v.achievements,
            fc=v.fc,
            fs=v.fs,
            rate=v.rate,
            dx_score=v.dx_score,
            level_value=calc_ds(v.dx_rating, v.achievements)
        )
    return r