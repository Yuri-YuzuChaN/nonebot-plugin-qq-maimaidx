from pathlib import Path

import nonebot
from nonebot.plugin import PluginMetadata, require

from .commands import *
from .config import BaseConfig, dfconfig, driver, log, maiconfig
from .core.database.qq import create_database as qq_create
from .core.image.update_table import UpdateTable
from .core.service import mai
from .web import *

scheduler = require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-qq-maimaidx",
    description="移植自 mai-bot 开源项目，基于 nonebot2 的街机音游 舞萌DX 的查询插件",
    usage="请使用 帮助maimaiDX 指令查看使用方法",
    type="application",
    config=BaseConfig,
    homepage="https://github.com/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx",
    supported_adapters={"~qq"}
)


sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)


@driver.on_startup
async def get_music():
    """
    bot启动时开始获取所有数据
    """
    await qq_create()
    if dfconfig.divingfish_prober_proxy:
        log.info("使用代理服务器访问「水鱼」查分器")
    if maiconfig.maimaidx_alias_proxy:
        log.info("使用代理服务器访问「柚子」别名服务器")
    log.info("正在获取maimai曲目数据")
    await mai.get_music()
    log.info("正在获取maimai曲目别名数据")
    await mai.get_music_alias()
    log.info("正在获取maimai牌子数据")
    await mai.get_plate_json()
    log.success("maimai数据获取完成")


scheduler.add_job(mai.update, "cron", hour=4)