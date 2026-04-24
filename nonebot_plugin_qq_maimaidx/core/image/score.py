from io import BytesIO

from PIL import Image

from ...config import maiconfig
from ...resources import pic_dir
from ..merge.models.score import *
from ..merge.models.service import ServiceName
from ..merge.models.song import SimpleSong, Song
from .base import ScoreBaseImage, change_column_width, coloum_width
from .tools import image_to_bytesio, song_chart


class DrawScore(ScoreBaseImage):
    
    def __init__(self, service: ServiceName, image: Image.Image) -> None:
        self.service = service
        super().__init__(image)
        self._im.alpha_composite(self._aurora_bg)
        self._im.alpha_composite(self._shines_bg, (34, 0))
        self._im.alpha_composite(self._cloud_bg, (319, self._im.size[1] - 643))
        self._im.alpha_composite(self._rainbow_bottom_bg, (100, self._im.size[1] - 343))
        for h in range((self._im.size[1] // 358) + 1):
            self._im.alpha_composite(self._pattern_bg, (0, (358 + 7) * h))

    def _while_pic(self, data: list[SimpleSong], y: int = 200):
        """
        循环绘制谱面
        
        Params:
            `data`: `谱面数据`
            `y`: `y轴坐标`
        """
        dy = 65
        x = 0
        for n, v in enumerate(data):
            if n % 20 == 0:
                x = 55
                y += dy if n != 0 else 0
            else:
                x += 65
            cover = Image.open(song_chart(v.song_id)).resize((55, 55))
            self._im.alpha_composite(cover, (x, y))
            self._im.alpha_composite(self._id_diff_im[int(v.difficulties.level)], (x, y + 45))
            self._tb.draw(
                x + 27, y + 50, 10, v.song_id, 
                self._diff_text_color[int(v.difficulties.level)], "mm"
            )
    
    def whilerisepic(self, data: list[RiseResult], low_score: int, isdx: bool):
        """
        循环绘制上分推荐数据
        
        Params:
            `data`: `上分数据`
            `low_score`: `最低分`
            `isdx`: `是否DX版本`
        """
        y = 120
        for index, _d in enumerate(data):
            x = 200 if isdx else 700
            y += 140 if index != 0 else 0
            
            rate = Image.open(pic_dir / f"UI_TTR_Rank_{_d.rate}.png").resize((63, 28))
            
            self._im.alpha_composite(self._rise_bg[_d.level_index], (x + 30, y))
            self._im.alpha_composite(
                Image.open(song_chart(_d.song_id)).resize((80, 80)), (x + 55, y + 40)
            )
            self._im.alpha_composite(
                Image.open(pic_dir / f"{_d.type.upper()}.png").resize((60, 22)), (x + 240, y + 114)
            )
            if _d.oldrate:
                oldrate = Image.open(pic_dir / f"UI_TTR_Rank_{_d.oldrate}.png").resize((63, 28))
                self._im.alpha_composite(oldrate, (x + 145, y + 82))
            self._im.alpha_composite(rate, (x + 305, y + 82))
            
            title = _d.song_name
            if coloum_width(title) > 26:
                title = change_column_width(title, 25) + "..."
            self._sy.draw(
                x + 142, y + 44, 17, title, 
                self._diff_text_color[_d.level_index], "lm"
            )
            self._tb.draw(
                x + 145, y + 124, 18, f"ID: {_d.song_id}", 
                self._id_text_color[_d.level_index], "lm"
            )
            self._tb.draw(
                x + 210, y + 71, 25, f"{_d.oldachievements:.4f}%", 
                self._diff_text_color[_d.level_index], anchor="mm"
            )
            self._tb.draw(
                x + 245, y + 96, 17, f"Ra: {_d.oldrating}", 
                self._diff_text_color[_d.level_index], anchor="mm"
            )
            self._tb.draw(
                x + 370, y + 71, 25, f"{_d.achievements:.4f}%", 
                self._diff_text_color[_d.level_index], anchor="mm"
            )
            self._tb.draw(
                x + 415, y + 96, 17, f"Ra: {_d.rating}", 
                self._diff_text_color[_d.level_index], anchor="mm"
            )
            self._tb.draw(
                x + 315, y + 124, 18, f"ds:{_d.rate}", 
                self._id_text_color[_d.level_index], anchor="lm"
            )
            if _d.oldrating > low_score:
                new_ra = _d.rating - _d.oldrating
            else:
                new_ra = _d.rating - low_score
            self._tb.draw(
                x + 390, y + 124, 18, f"Ra +{new_ra}", 
                self._id_text_color[_d.level_index], "lm"
            )
         
    def draw_rise(
        self, 
        sd: list[RiseResult], 
        sd_score: int, 
        dx: list[RiseResult], 
        dx_score: int
    ) -> Image.Image:
        """
        绘制上分数据表
        
        Params:
            `sd`: `旧版本谱面`
            `sd_score`: `旧版本最低分`
            `sd`: `新版本谱面`
            `dx_score`: `新版本最低分`
        Returns:
            `Image.Image`
        """
        title_bg = self._title_bg.copy().resize((273, 80))
        self._im.alpha_composite(title_bg, (314, 30))
        self._sy.draw(450, 68, 18, "旧版本谱面推荐", self._default_text_color, "mm")
        self.whilerisepic(sd, sd_score, True)
        self._im.alpha_composite(title_bg, (814, 30))
        self._sy.draw(950, 68, 18, "新版本谱面推荐", self._default_text_color, "mm")
        self.whilerisepic(dx, dx_score, False)
        
        height = self._im.size[1]
        self._im.alpha_composite(self._design_circle_bg.resize((800, 72)), (300, height - 110))
        self._sy.draw(
            700, height - 76, 18, 
            f"Designed by Yuri-YuzuChaN & BlueDeer233. Generated by {maiconfig.bot_name} BOT", 
            self._default_text_color, "mm"
        )
        return self._im

    def draw_plan(
        self,
        completed: list[PlayedResult],
        completed_y: int,
        unfinished: list[PlayedResult],
        unfinished_y: int,
        notstarted: list[SimpleSong],
        plan: str,
        completed_len: int,
    ) -> Image.Image:
        """
        绘制进度表
        
        Params:
            `completed`: `已完成谱面`
            `completed_y`: `已完成谱面高度`
            `unfinished`: `未完成谱面`
            `unfinished_y`: `未完成谱面高度`
            `notstarted`: `未游玩谱面`
            `plan`: `目标`
            `completed_len`: `已完成谱面数量`
        Returns:
            `Image.Image`
        """
        max = len(completed + unfinished + notstarted)

        self._im.alpha_composite(self._title_lengthen_bg, (475, 30))
        self._im.alpha_composite(self._title_lengthen_bg, (475, 30 + completed_y))
        self._im.alpha_composite(self._title_lengthen_bg, (475, 30 + completed_y + unfinished_y))
        
        self._sy.draw(
            700, 77, 22, f"已完成谱面「{len(completed)}」个", 
            self._default_text_color, "mm"
        )
        self._sy.draw(
            700, 77 + completed_y, 22, f"未完成谱面「{len(unfinished)}」个", 
            self._default_text_color, "mm"
        )
        self._sy.draw(
            700, 77 + completed_y + unfinished_y, 22, f"未游玩谱面「{len(notstarted)}」个", 
            self._default_text_color, "mm"
        )
        
        self.whiledraw(completed[:completed_len], False, 140)
        self.whiledraw(unfinished[:30], False, 140 + completed_y)
        self._while_pic(notstarted[:100], 140 + completed_y + unfinished_y)

        self._im.alpha_composite(self._design_circle_bg, (200, self._im.size[1] - 113))
        pagemsg = f"共计「{max}」个谱面，剩余「{len(unfinished + notstarted)}」个谱面未完成「{plan.upper()}」"
        self._sy.draw(700, self._im.size[1] - 70, 25, pagemsg, self._default_text_color, "mm")
        return self._im

    def draw_category(
        self, 
        CATEGORY: str, 
        data: list[PlayedResult] | list[SimpleSong],
        page: int = 1, 
        end_page: int = 1
    ) -> Image.Image:
        """
        绘制指定进度表
        
        Params:
            `CATEGORY`: `类别`
            `data`: `数据`
            `page`: `页数`
            `end_page`: `总页数`
        Returns:
            `Image.Image`
        """
        lendata = len(data)
        newdata = data[(page - 1) * 80: page * 80]
        self._im.alpha_composite(self._title_lengthen_bg, (475, 30))
        if CATEGORY == "completed" or CATEGORY == "unfinished":
            txt = "已完成" if CATEGORY == "completed" else "未完成"
            self._sy.draw(700, 77, 28, f"{txt}谱面", self._default_text_color, "mm")
            self.whiledraw(newdata, False, 140)
            self._im.alpha_composite(self._design_circle_bg, (200, self._im.size[1] - 113))
            
            pagemsg = (
                f"{txt}谱面共计「{lendata}」个，"
                f"展示第「{(page - 1) * 80 + 1}-{80 * (page - 1) + len(newdata)}」个，"
                f"当前第「{page} / {end_page}」页"
            )
            self._sy.draw(700, self._im.size[1] - 70, 25, pagemsg, self._default_text_color, "mm")
        else:
            self._sy.draw(700, 105, 28, "未游玩谱面", self._default_text_color, "mm")
            self._while_pic(data)
            self._im.alpha_composite(self._design_circle_bg, (200, self._im.size[1] - 113))
            self._sy.draw(
                700, self._im.size[1] - 70, 25, f"未游玩谱面共计「{len(data)}」个", 
                self._default_text_color, "mm"
            )
        return self._im
    
    def draw_score_list(
        self, 
        rating: str | float, 
        play_result: list[PlayedResult], 
        page: int, 
        end_page: int
    ) -> BytesIO:
        """
        绘制分数列表
        
        Params:
            `rating`: `定数`
            `play_result`: `游玩成绩`
            `page`: `页数`
            `end_page`: `总页数`
        Returns:
            `Image.Image`
        """
        start_offset = (page - 1) * 80
        current_page_result = play_result[start_offset : page * 80]
        
        self._im.alpha_composite(self._title_lengthen_bg, (525, 30))
        
        no_start = start_offset + 1
        no_end = start_offset + len(current_page_result)
        self._sy.draw(
            750, 80, 28, f"No.{no_start}- No.{no_end}", 
            self._default_text_color, "mm"
        )
        
        self.whiledraw(current_page_result, False, 100, 140)
        
        for num in range(len(current_page_result)):
            if num % 20 == 0:
                section_num = num // 20
                _y = 140 + (num // 5) * 109
                side_text = f"No.「{section_num * 20 + 1}-{num + 20}」"
                self._fot.draw(50, _y + 50, 22, side_text, self._default_text_color, "mm")

        self._im.alpha_composite(self._design_circle_bg, (250, self._im.size[1] - 113))
        
        footer_text = (
            f"「{rating}」共计「{len(play_result)}」个成绩，"
            f"当前第「{no_start}-{no_end}」个，"
            f"第「{page} / {end_page}」页"
        )
        self._sy.draw(700, self._im.size[1] - 70, 25, footer_text, self._default_text_color, "mm")
        return image_to_bytesio(self._im)