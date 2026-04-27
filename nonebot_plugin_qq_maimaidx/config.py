from typing import Literal

from loguru import logger as log
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel

driver = get_driver()

class BaseConfig(BaseModel):
    
    priority_data_source: Literal["Lxns-Network", "Diving-Fish"]
    maimaidx_path: str
    maimaidx_alias_proxy: bool = False
    assets_online: bool = False
    bot_name: str = list(driver.config.nickname)[0] if driver.config.nickname else "百合咲Mika"

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