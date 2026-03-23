import asyncio

from ...config import alias_file, log
from ..clients.exceptions import ServerError
from ..clients.yuzuchan.client import YuzuChaNAPI
from ..clients.yuzuchan.models import Alias
from ..tool import openfile, writefile

aliaserror = (
    "本地暂存别名文件为空，请自行使用浏览器访问" 
    "「https://www.yuzuchan.moe/api/maimaidx/maimaidxalias」"
    "获取别名数据并保存在 'static/music_alias.json' 文件中并重启bot"
)


async def get_music_alias_list() -> list[Alias]:
    """获取所有别名"""
    alias_data: list[dict[str, int | str | list[str]]] = []
    try:
        raise ServerError
        api = YuzuChaNAPI()
        alias_data = await api.get_alias()
        await writefile(alias_file, alias_data)
    except asyncio.exceptions.TimeoutError:
        log.error("获取别名超时，已切换至本地暂存文件")
        alias_data = await openfile(alias_file)
        if not alias_data:
            log.error(aliaserror)
            raise ValueError
    except ServerError as e:
        log.error(str(e) + "。已切换至本地暂存文件")
        alias_data = await openfile(alias_file)
    except Exception:
        log.error("获取所有曲目别名信息错误，请检查网络环境。已切换至本地暂存文件")
        alias_data = await openfile(alias_file)
        if not alias_data:
            log.error(aliaserror)
            raise ValueError
    
    return [Alias.model_validate(_a) for _a in alias_data]


async def get_plate_data():
    api = YuzuChaNAPI()
    return await api.get_plate_json()