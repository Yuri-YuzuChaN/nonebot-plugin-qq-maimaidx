from pathlib import Path

from loguru import logger as log
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel

driver = get_driver()

class BaseConfig(BaseModel):
    
    maimaidx_path: str
    maimaidx_alias_proxy: bool = False
    assets_online: bool = False
    botname: str = list(driver.config.nickname)[0] if driver.config.nickname else "百合咲Mika"
    

class DivingFishConfig(BaseModel):

    divingfish_prober_proxy: bool = False
    divingfish_token: str | None = None


class LxnsConfig(BaseModel):
    
    lxns_dev_token: str | None = None
    lx_client_id: str | None = None
    lx_client_secret: str | None = None
    redirect_uri: str | None = None


maiconfig = get_plugin_config(BaseConfig)
dfconfig = get_plugin_config(DivingFishConfig)
lxnsconfig = get_plugin_config(LxnsConfig)


# echartsjs
SNAPSHOT_JS = (
    "echarts.getInstanceByDom(document.querySelector('div[_echarts_instance_]'))."
    "getDataURL({type: 'PNG', pixelRatio: 2, excludeComponents: ['toolbox']})"
)


Root = Path(__file__).parent

if maiconfig.maimaidx_path:
    static = Path(maiconfig.maimaidx_path)
else:
    raise ValueError(
        "`nonebot-plugin-maimaidx` 插件未检测到静态文件夹 `static`，"
        "请根据 README 配置页说明进行下载静态文件"
    )


# 静态资源路径
font_dir    = static / "font"
data_dir    = static / "data"
pic_dir     = static / "mai" / "pic"
cover_dir   = static / "mai" / "cover"
rating_dir  = static / "mai" / "rating"
plate_dir   = static / "mai" / "plate"

# 路径文件
pie_html_file       = static / "temp_pie.html"              # 饼图html文件
alias_file          = data_dir / "music_alias.json"         # 别名暂存文件
lxns_alias_file     = data_dir / "lxns_music_alias.json"    # 别名暂存文件
music_file          = data_dir / "music_data.json"          # 曲目暂存文件
lxns_music_file     = data_dir / "lxns_music_data.json"     # 曲目暂存文件
chart_file          = data_dir / "music_chart.json"         # 谱面数据暂存文件
merge_music_file    = data_dir / "merge_music_data.json"    # 合并曲目数据文件
merge_alias_file    = data_dir / "merge_music_alias.json"   # 合并曲目别名数据文件


# 字体路径
SIYUAN =  font_dir / "ResourceHanRoundedCN-Bold.ttf"
SHANGGUMONO = font_dir / "ShangguMonoSC-Regular.otf"
TBFONT = font_dir / "Torus SemiBold.otf"
FOTNEWRODIN = font_dir / "FOT-NewRodin Pro EB.otf"


# 常用变量
SONGS_PER_PAGE = 25
RANK_SP = [
    "d", "c", "b", "bb", "bbb", "a", "aa", 
    "aaa", "s", "sp", "ss", "ssp", "sss", "sssp"
]
RANK_PLUS = [k.replace("p", "+") for k in RANK_SP]
RANK_MAP = {
    k: (k[:-1].upper() + "p" if k.endswith("p") else k.upper())
    for k in RANK_SP
}

COMBO_SP = ["fc", "fcp", "ap", "app"]
COMBO_PLUS = [k.replace("p", "+") for k in COMBO_SP]
COMBO_MAP = {
    k: (k[:-1].upper() + "p" if k.endswith("p") else k.upper())
    for k in COMBO_SP
}

SYNC_D_SP = ["fs", "fsp", "fsd", "fsdp"]
SYNC_SP = ["fs", "fsp", "fdx", "fdxp"]
SYNC_PLUS = [k.replace("p", "+") for k in SYNC_SP]
SYNC_MAP = {
    "fs": "FS", 
    "fsp": "FSp", 
    "fsd": "FSD", 
    "fdx": "FSD", 
    "fsdp": "FSDp", 
    "fdxp": "FSDp", 
    "sync": "Sync"
}

DIFFS = ["Basic", "Advanced", "Expert", "Master", "Re:Master"]
LEVEL_LIST = [
    "1", 
    "2", 
    "3", 
    "4", 
    "5", 
    "6", 
    "7", 
    "7+", 
    "8", 
    "8+", 
    "9", 
    "9+", 
    "10", 
    "10+", 
    "11", 
    "11+", 
    "12", 
    "12+", 
    "13", 
    "13+", 
    "14", 
    "14+", 
    "15"
]
ACHIEVEMENT_LIST = [
    50.0, 60.0, 70.0, 75.0, 80.0, 90.0,
    94.0, 97.0, 98.0, 99.0, 99.5, 100.0, 100.5
]
BASE_RA_SPP = [
    7.0, 8.0, 9.6, 11.2, 12.0, 13.6,
    15.2, 16.8, 20.0, 20.3, 20.8, 21.1, 21.6, 22.4
]
SD_VERSION = {
    "初": "maimai",
    "真": "maimai PLUS",
    "超": "maimai GreeN",
    "檄": "maimai GreeN PLUS",
    "橙": "maimai ORANGE",
    "暁": "maimai ORANGE PLUS",
    "晓": "maimai ORANGE PLUS",
    "桃": "maimai PiNK",
    "櫻": "maimai PiNK PLUS",
    "樱": "maimai PiNK PLUS",
    "紫": "maimai MURASAKi",
    "菫": "maimai MURASAKi PLUS",
    "堇": "maimai MURASAKi PLUS",
    "白": "maimai MiLK",
    "雪": "MiLK PLUS",
    "輝": "maimai FiNALE",
    "辉": "maimai FiNALE"
}
DX_VERSION = {
    **SD_VERSION,
    "熊": "maimai でらっくす",
    "華": "maimai でらっくす PLUS",
    "华": "maimai でらっくす PLUS",
    "爽": "maimai でらっくす Splash",
    "煌": "maimai でらっくす Splash PLUS",
    "宙": "maimai でらっくす UNiVERSE",
    "星": "maimai でらっくす UNiVERSE PLUS",
    "祭": "maimai でらっくす FESTiVAL",
    "祝": "maimai でらっくす FESTiVAL PLUS",
    "双": "maimai でらっくす BUDDiES",
    "宴": "maimai でらっくす BUDDiES PLUS",
    "镜": "maimai でらっくす PRiSM",
    "彩": "maimai でらっくす PRiSM PLUS"
}
VERSION_MAP = {
    "真": ([DX_VERSION["真"], DX_VERSION["初"]], "真"),
    "超": ([SD_VERSION["超"]], "超"),
    "檄": ([SD_VERSION["檄"]], "檄"),
    "橙": ([SD_VERSION["橙"]], "橙"),
    "暁": ([SD_VERSION["暁"]], "暁"),
    "桃": ([SD_VERSION["桃"]], "桃"),
    "櫻": ([SD_VERSION["櫻"]], "櫻"),
    "紫": ([SD_VERSION["紫"]], "紫"),
    "菫": ([SD_VERSION["菫"]], "菫"),
    "白": ([SD_VERSION["白"]], "白"),
    "雪": ([SD_VERSION["雪"]], "雪"),
    "輝": ([SD_VERSION["輝"]], "輝"),
    "霸": (list(set(SD_VERSION.values())), "舞"),
    "舞": (list(set(SD_VERSION.values())), "舞"),
    "熊": ([DX_VERSION["熊"]], "熊&华"),
    "华": ([DX_VERSION["熊"]], "熊&华"),
    "華": ([DX_VERSION["熊"]], "熊&华"),
    "爽": ([DX_VERSION["爽"]], "爽&煌"),
    "煌": ([DX_VERSION["爽"]], "爽&煌"),
    "宙": ([DX_VERSION["宙"]], "宙&星"),
    "星": ([DX_VERSION["宙"]], "宙&星"),
    "祭": ([DX_VERSION["祭"]], "祭&祝"),
    "祝": ([DX_VERSION["祭"]], "祭&祝"),
    "双": ([DX_VERSION["双"]], "双&宴"),
    "宴": ([DX_VERSION["双"]], "双&宴"),
    "镜": ([DX_VERSION["镜"]], "镜&彩"),
    "彩": ([DX_VERSION["镜"]], "镜&彩")
}
PLATE_CN = {
    "晓": "暁",
    "樱": "櫻",
    "堇": "菫",
    "辉": "輝",
    "华": "華"
}
CATEGORY = {
    "流行&动漫": "anime",
    "舞萌": "maimai",
    "niconico & VOCALOID": "niconico",
    "东方Project": "touhou",
    "其他游戏": "game",
    "音击&中二节奏": "ongeki",
    "POPSアニメ": "anime",
    "maimai": "maimai",
    "niconicoボーカロイド": "niconico",
    "東方Project": "touhou",
    "ゲームバラエティ": "game",
    "オンゲキCHUNITHM": "ongeki",
    "宴会場": "宴会场"
}