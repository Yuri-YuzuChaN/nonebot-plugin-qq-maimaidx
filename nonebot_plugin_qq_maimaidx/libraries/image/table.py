from collections import defaultdict

from ...config import *
from ..domain.models.score import PlayResult, RatingTableResult
from ..domain.models.service import ServiceName
from ..utils.calc import compute_rating
from .base import *
from .tools import *

PlayedResultMap = defaultdict[int, dict[int, RatingTableResult]]
PlateResultMap = dict[str, dict[int, list[PlayResult | None]]]


STATISTICS_KEYS = [
    "clear", "sync", "s", "sp", "ss", "ssp", "sss", "sssp",
    "fc", "fcp", "ap", "app", "fs", "fsp", "fsd", "fsdp"
]


class RatingGridConfig:
    
    start_x = 158
    """作图 `x` 轴起点"""
    start_y = 118
    """作图 `y` 轴起点"""
    gap_x = 85
    """`x` 轴间距"""
    gap_y = 85
    """`y` 轴间距"""
    row_count = 14
    """`x` 轴数量"""
    stats_start_x = 824
    """统计数据 `x` 轴起点"""
    stats_start_y = 22
    """统计数据 `y` 轴起点"""
    stats_col_count = 8
    """统计数据横向数量"""


class PlateGridConfig:
    
    start_x = 200
    """作图 `x` 轴起点"""
    start_y = 245
    """作图 `y` 轴起点"""
    gap = 115
    """`x` 和 `y` 轴间距"""
    row_count = 10
    """数量"""
    stats_start_x = 390
    """统计数据 `x` 轴起点"""
    stats_start_y = 270
    """统计数据 `y` 轴起点"""
    stats_gap_x = 200
    """统计数据 `x` 轴间距"""


class DrawRatingTable:
    
    # rating_bg = Image.open(pic_dir / "rating_bg.png")
    unfinished_bg = Image.open(pic_dir / "unfinished_bg.png")
    complete_bg = Image.open(pic_dir / "complete_bg.png")
    
    def __init__(
        self, 
        service: ServiceName, 
        play_result: list[PlayResult],
        *,
        rating: str | None = None,
        is_fc: bool = False
    ):
        self.service = service
        self.result = play_result
        self.rating = rating
        self.is_fc = is_fc
        
        self._rank_cache: dict[str, Image.Image] = {}
        self._fc_cache: dict[str, Image.Image] = {}
    
    def _get_rank_icon(self, rate: str) -> Image.Image:
        """按需加载并缓存图标"""
        if rate not in self._rank_cache:
            path = pic_dir / f"UI_TTR_Rank_{rate}.png"
            if path.exists():
                self._rank_cache[rate] = Image.open(path)
        return self._rank_cache.get(rate)
    
    def _get_fc_icon(self, fc: str) -> Image.Image:
        if fc not in self._fc_cache:
            path = pic_dir / f"UI_MSS_MBase_Icon_{COMBO_MAP[fc]}.png"
            if path.exists():
                self._fc_cache[fc] = Image.open(path).resize((50, 50))
        return self._fc_cache.get(fc)
    
    def _calc_achievements_fc(
        self, 
        score_list: list[float] | list[str], 
        lvlist_num: int
    ) -> int:
        r = -1
        thresholds = range(4) if self.is_fc else ACHIEVEMENT_LIST[-6:]
        for _t in thresholds:
            count = sum(1 for s in score_list if s >= _t)
            if count == lvlist_num:
                r += 1
            else:
                break
        return r
    
    def _process_rating_table_data(self) -> tuple[dict[str, int], PlayedResultMap]:
        """
        处理定数表数据
        """
        statistics = {k: 0 for k in STATISTICS_KEYS}
        played_map: PlayedResultMap = defaultdict(dict)
        rank_sp = RANK_SP[-6:]
        
        for _d in self.result:
            if _d.level != self.rating:
                continue
            played_map[_d.song_id][_d.level_index] = RatingTableResult(
                achievements=_d.achievements,
                level=_d.level,
                fc=_d.fc
            )
            rate = compute_rating(_d.level_value, _d.achievements, onlyrate=True).lower()
            if _d.achievements >= 80:
                statistics["clear"] += 1
            
            if rate in rank_sp:
                for r in rank_sp[:rank_sp.index(rate) + 1]:
                    statistics[r] += 1
            
            if _d.fc and _d.fc in COMBO_SP:
                for f in COMBO_SP[:COMBO_SP.index(_d.fc) + 1]:
                    statistics[f] += 1
                    
            if _d.fs:
                if _d.fs == "sync":
                    statistics["sync"] += 1
                elif _d.fs in SYNC_D_SP:
                    for s in SYNC_D_SP[:SYNC_D_SP.index(_d.fs) + 1]:
                        statistics[s] += 1
        
        return statistics, played_map
    
    def draw(self) -> BytesIO:
        """
        绘制定数表
        """
        statistics, played_map = self._process_rating_table_data()
        
        lv_data = mai.total_level_data.get(self.rating)
        total_songs_count = sum(len(v) for v in lv_data.values())
        achievements_fc_list: list[float | int] = []
        
        im = Image.open(rating_dir / f"{self.rating}.png").convert("RGBA")
        dr = ImageDraw.Draw(im)
        sy = DrawText(dr, SIYUAN)
        tb = DrawText(dr, TBFONT)
        
        default_color = (124, 129, 255, 255)
        
        # im.alpha_composite(self.rating_bg, (600, 25))
        sy.draw(305, 60, 65, f"Level.{self.rating}", default_color, "mm", 5, (255, 255, 255, 255))
        sy.draw(305, 130, 65, "定数表", default_color, "mm", 5, (255, 255, 255, 255))
        tb.draw(700, 130, 45, total_songs_count, default_color, "mm", 5, (255, 255, 255, 255))
        
        for n, key in enumerate(STATISTICS_KEYS):
            row, col = divmod(n, RatingGridConfig.stats_col_count)
            x = RatingGridConfig.stats_start_x + col * 64
            y = RatingGridConfig.stats_start_y + row * 56
            tb.draw(x, y, 20, statistics[key], default_color, "mm", 2, (255, 255, 255, 255))
        
        current_y = RatingGridConfig.start_y
        for ra, songs in lv_data.items():
            current_y += 20
            for num, song in enumerate(lv_data[ra]):
                row, col = divmod(num, RatingGridConfig.row_count)
                x = RatingGridConfig.start_x + col * RatingGridConfig.gap_x
                y = current_y + row * RatingGridConfig.gap_y
                
                record = played_map.get(song.song_id).get(song.difficulties.level)
                
                if record is None:
                    continue
                if not self.is_fc:
                    achievements_fc_list.append(record.achievements)
                    bg = self.complete_bg if record.achievements >= 100 else self.unfinished_bg
                    im.alpha_composite(bg, (x + 2, y - 18))
                    
                    rate = compute_rating(
                        song.difficulties.level_value, 
                        record.achievements, 
                        onlyrate=True
                    )
                    im.alpha_composite(self._get_rank_icon(rate).resize((78, 35)), (x, y - 5))
                    continue
                if record.fc:
                    achievements_fc_list.append(COMBO_SP.index(record.fc))
                    im.alpha_composite(self.complete_bg, (x + 2, y - 18))
                    im.alpha_composite(self._get_fc_icon(record.fc), (x + 15, y - 12))
                        
            group_rows = (len(songs) - 1) // RatingGridConfig.row_count + 1
            current_y += group_rows * RatingGridConfig.gap_y

        if len(achievements_fc_list) == total_songs_count:
            r = self._calc_achievements_fc(achievements_fc_list, total_songs_count)
            if r != -1:
                pic = COMBO_MAP[COMBO_SP[r]] if self.is_fc else RANK_MAP[RANK_SP[-6:][r]]
                im.alpha_composite(Image.open(pic_dir / f"UI_MSS_Allclear_Icon_{pic}.png"), (40, 40))
        
        
        final_im = im.resize((int(im.size[0] * 0.8), int(im.size[1] * 0.8)), Image.Resampling.LANCZOS)
        return image_to_bytesio(final_im)


class DrawPlateTable:
    
    PLAN_CRITERIA: dict[str, dict[str, str | list[str] | int]] = {
        "极": {"attr": "fc", "values": COMBO_SP, "prefix": "UI_CHR_PlayBonus_"},
        "極": {"attr": "fc", "values": COMBO_SP, "prefix": "UI_CHR_PlayBonus_"},
        "将": {"attr": "achievements", "values": 100, "prefix": "RANK"},
        "神": {"attr": "fc", "values": ["ap", "app"], "prefix": "UI_CHR_PlayBonus_"},
        "舞舞": {
            "attr": "fs", 
            "values": ["fsd", "fsdp", "fsdpx", "fsdp+"], 
            "prefix": "UI_CHR_PlayBonus_"
        },
    }
    
    finished_bg = [Image.open(pic_dir / f"t-{_}.png") for _ in range(4)]
    unfinished_bg = Image.open(pic_dir / "unfinished_bg_2.png")
    complete_bg = Image.open(pic_dir / "complete_bg_2.png")
    
    def __init__(
        self, 
        service: ServiceName, 
        play_result: list[PlayResult],
        *,
        plan: str | None = None,
        version_name: str | None = None
    ):
        self.service = service
        self.result = play_result
        self.plan = plan
        self.version_name = version_name
    
    def _is_qualified(self, play: PlayResult | None, plan: str) -> bool:
        """判定单个谱面是否符合牌子要求"""
        if not play: return False
        cfg = self.PLAN_CRITERIA.get(plan)
        if not cfg: return False
        
        val = getattr(play, cfg["attr"])
        if plan == "将":
            return val >= 100
        return val in cfg["values"]

    def _get_plate_icon(self, play: PlayResult, plan: str) -> Image.Image:
        """获取牌子主格的大图标"""
        if plan == "将":
            rate = compute_rating(play.level_value, play.achievements, onlyrate=True)
            return Image.open(pic_dir / f"UI_TTR_Rank_{rate}.png").resize((102, 46))
        
        cfg = self.PLAN_CRITERIA.get(plan)
        val = getattr(play, cfg["attr"])
        
        icon_name = COMBO_MAP.get(val) or SYNC_MAP.get(val) or val
        path = pic_dir / f"{cfg['prefix']}{icon_name}.png"
        return Image.open(path).resize((75, 75)) if path.exists() else None
    
    def _process_plate_table_data(self) -> tuple[int, PlateResultMap]:
        """
        处理牌子表数据
        """
        plate_id_list = mai.total_plate_id_list[self.version_name]
        song_list = mai.total_list.by_id_list(plate_id_list)
        
        slot_num = 5 if self.version_name in ["霸", "舞"] else 4
        played_map: PlateResultMap = defaultdict(lambda: defaultdict(lambda: [None] * slot_num))
        
        song_list.sort(key=lambda x: x.difficulties[3].level_value, reverse=True)
        for song in song_list:
            played_map[song.difficulties[3].level][song.song_id]
        
        for _d in self.result:
            if slot_num == 4 and _d.level_index == 4:
                continue
            played_map[_d.level][_d.song_id][_d.level_index] = _d
        
        return len(plate_id_list), played_map
    
    def draw(self) -> BytesIO:
        """
        绘制完成表
        """
        slot_num = 5 if self.version_name in ["霸", "舞"] else 4
        plate_total_count, played_map = self._process_plate_table_data()
        
        im = Image.open(plate_dir / f"{self.version_name}.png")
        draw = ImageDraw.Draw(im)
        tr = DrawText(draw, TBFONT)
        mr = DrawText(draw, SIYUAN)
        
        plate_bg = plate_dir / f"{self.version_name}{'極' if self.plan == '极' else self.plan}.png"
        im.alpha_composite(Image.open(plate_bg).resize((1000, 161)), (200, 35))
        lv = [set() for _ in range(slot_num)]
        
        current_y = PlateGridConfig.start_y
        for index, songs_dict in played_map.items():
            current_y += 15
            for idx, (song_id, result) in enumerate(songs_dict.items()):
                row, col = divmod(idx, PlateGridConfig.row_count)
                cur_x = PlateGridConfig.start_x + col * PlateGridConfig.gap
                cur_y = current_y + row * PlateGridConfig.gap
                
                hit_slots = []
                for i, play in enumerate(result):
                    if self._is_qualified(play, self.plan):
                        hit_slots.append(i)
                        lv[i].add(song_id)
                
                if 3 in hit_slots:
                    play = result[3]
                    im.alpha_composite(self.complete_bg, (cur_x, cur_y))
                    
                    icon = self._get_plate_icon(play, self.plan)
                    if icon:
                        im.alpha_composite(icon, (cur_x + 13, cur_y + 3))

                for s_idx in hit_slots:
                    if s_idx < len(self.finished_bg):
                        im.alpha_composite(self.finished_bg[s_idx], (cur_x + 5 + 25 * s_idx, cur_y + 67))

            rows = (len(songs_dict) - 1) // PlateGridConfig.row_count + 1
            current_y += rows * PlateGridConfig.gap
        
        colors = [(124, 129, 255, 255)] + ScoreBaseImage._id_text_color
        
        for i in range(len(lv) + 1):
            x = PlateGridConfig.stats_start_x + i * PlateGridConfig.stats_gap_x
            y = PlateGridConfig.stats_start_y
            
            if i == 0:
                intersection = set.intersection(*lv) if lv else set()
                val_str = f"{len(intersection)}/{plate_total_count}"
            else:
                val_str = str(len(lv[i-1]))
            
            if str(len(lv[i-1]) if i > 0 else len(intersection)) == str(plate_total_count):
                mr.draw(x, y, 35, "完成", colors[i], "rm", 4, (255, 255, 255, 255))
            else:
                tr.draw(x, y, 40, val_str, colors[i], "rm", 4, (255, 255, 255, 255))

        return image_to_bytesio(im)