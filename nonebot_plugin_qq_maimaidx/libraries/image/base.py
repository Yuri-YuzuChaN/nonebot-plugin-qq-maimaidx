from PIL import Image, ImageDraw

from ...config import *
from ..clients.lxns.models.enum import SongType
from ..domain.models.score import PlayResult
from ..service import mai
from ..utils.calc import calc_ds, dx_score
from .tools import DrawText, song_chart


def get_char_width(o: int) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), 
        (1154, 1), (1161, 0), (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), 
        (8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2), (12351, 1), (12438, 2), 
        (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1), (64106, 2), (65039, 1), 
        (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2), (120831, 1), 
        (262141, 2), (1114109, 1)
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloum_width(s: str) -> int:
    res = 0
    for ch in s:
        res += get_char_width(ord(ch))
    return res


def change_column_width(s: str, len: int) -> str:
    res = 0
    slist = []
    for ch in s:
        res += get_char_width(ord(ch))
        if res <= len:
            slist.append(ch)
    return "".join(slist)


class ScoreBaseImage:
    
    _default_text_color = (124, 129, 255, 255)
    _diff_text_color = [
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (138, 0, 226, 255)
    ]
    _id_text_color = [
        (129, 217, 85, 255), 
        (245, 189, 21, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (138, 0, 226, 255)
    ]
    _bg_color = [
        (111, 212, 61, 255), 
        (248, 183, 9, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (219, 170, 255, 255)
    ]
    
    # 预存图片
    _id_diff_im = [Image.new("RGBA", (55, 10), color) for color in _bg_color]
    _dx_star_bg = [Image.open(pic_dir / f"UI_GAM_Gauge_DXScoreIcon_0{num}.png") for num in range(1, 6)]
    _diff_bg = [
        Image.open(pic_dir / "b50_score_basic.png"), 
        Image.open(pic_dir / "b50_score_advanced.png"), 
        Image.open(pic_dir / "b50_score_expert.png"), 
        Image.open(pic_dir / "b50_score_master.png"), 
        Image.open(pic_dir / "b50_score_remaster.png")
    ]
    _rise_bg = [
        Image.open(pic_dir / "rise_score_basic.png"),
        Image.open(pic_dir / "rise_score_advanced.png"),
        Image.open(pic_dir / "rise_score_expert.png"),
        Image.open(pic_dir / "rise_score_master.png"),
        Image.open(pic_dir / "rise_score_remaster.png")
    ]
    _title_bg           = Image.open(pic_dir / "title.png")
    _title_lengthen_bg  = Image.open(pic_dir / "title-lengthen.png")
    _design_circle_bg   = Image.open(pic_dir / "design_circle.png")
    _design_prism_bg    = Image.open(pic_dir / "design_prism.png")
    _separator_bg       = Image.open(pic_dir / "separator.png")
    _chart_white_bg     = Image.open(pic_dir / "chart_white_bg.png")
    _level_bg           = Image.open(pic_dir / "UI_CMN_Chara_Level_S_01.png")
    _cloud_bg           = Image.open(pic_dir / "rainbow.png").convert("RGBA")
    _rainbow_bottom_bg  = Image.open(pic_dir / "rainbow_bottom.png").convert("RGBA")
    _aurora_bg          = Image.open(pic_dir / "aurora.png").convert("RGBA")
    _shines_bg          = Image.open(pic_dir / "bg_shines.png").convert("RGBA")
    _pattern_bg         = Image.open(pic_dir / "pattern.png").convert("RGBA")

    def __init__(self, image: Image.Image = None) -> None:
        self._im = image
        dr = ImageDraw.Draw(self._im)
        self._sy = DrawText(dr, SIYUAN)
        self._tb = DrawText(dr, TBFONT)
        self._fot = DrawText(dr, FOTNEWRODIN)
    
    def whiledraw(
        self, 
        data: list[PlayResult], 
        dx: bool, 
        height: int = 0
    ):
        # y为第一排纵向坐标，dy为各行间距
        dy = 114
        
        is_chart_data = bool(data) and isinstance(data[0], PlayResult)
        if is_chart_data:
            y = 1085 if dx else 235
        else:
            y = height
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 16
                y += dy if num != 0 else 0
            else:
                x += 276

            cover = Image.open(song_chart(info.song_id)).resize((75, 75))
            version = Image.open(pic_dir / f"{info.type.upper()}.png").resize((37, 14))
            if info.rate.islower():
                rate = Image.open(pic_dir / f"UI_TTR_Rank_{RANK_MAP[info.rate]}.png").resize((63, 28))
            else:
                rate = Image.open(pic_dir / f"UI_TTR_Rank_{info.rate}.png").resize((63, 28))

            self._im.alpha_composite(self._diff_bg[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 12, y + 12))
            self._im.alpha_composite(version, (x + 51, y + 91))
            self._im.alpha_composite(rate, (x + 92, y + 78))
            if info.fc:
                fc = Image.open(pic_dir / f"UI_MSS_MBase_Icon_{COMBO_MAP[info.fc]}.png").resize((34, 34))
                self._im.alpha_composite(fc, (x + 154, y + 77))
            if info.fs:
                fs = Image.open(pic_dir / f"UI_MSS_MBase_Icon_{SYNC_MAP[info.fs]}.png").resize((34, 34))
                self._im.alpha_composite(fs, (x + 185, y + 77))
            
            song = mai.total_list.by_id(info.song_id)
            dxscore = song.difficulties[info.level_index].dx_score
            if (dx_star := dx_score(info.dx_score / dxscore * 100)) != 0:
                self._im.alpha_composite(self._dx_star_bg[dx_star].resize((47, 26)), (x + 217, y + 80))

            self._tb.draw(x + 26, y + 98, 13, info.song_id, self._id_text_color[info.level_index], anchor="mm")
            title = info.song_name
            if coloum_width(title) > 18:
                title = change_column_width(title, 17) + "..."
            self._sy.draw(x + 93, y + 14, 14, title, self._diff_text_color[info.level_index], anchor="mm")
            self._tb.draw(x + 93, y + 38, 30, f"{info.achievements:.4f}%", self._diff_text_color[info.level_index], anchor="lm")
            self._tb.draw(x + 219, y + 65, 15, f"{info.dx_score}/{dxscore}", self._diff_text_color[info.level_index], anchor="mm")
            
            ds = calc_ds(info.rating, info.achievements)
            self._tb.draw(x + 93, y + 65, 15, f"{ds} -> {info.rating}", self._diff_text_color[info.level_index], anchor="lm")