from httpx import Response

from ....config import maiconfig
from ..exceptions import *
from ..http import ApiClient
from .models import *

DOMAIN_NAME = "site" if maiconfig.maimaidx_alias_proxy else "moe"


class YuzuChaNAPI(ApiClient):
    
    def __init__(self):
        super().__init__(
            base_url=f"https://www.yuzuchan.{DOMAIN_NAME}/api/maimaidx", 
        )
    
    def _handle_error(self, resp: Response) -> None:
        if resp.status_code == 200:
            return
        elif resp.status_code == 500:
            raise ServerError
        else:
            raise UnknownError
    
    async def _request_data(
        self,
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> APIResult:
        data = await self._request(method, endpoint, **kwargs)
        return APIResult.model_validate(data)
    
    async def get_plate_json(self) -> dict[str, list[int]]:
        """获取所有版本牌子完成需求"""
        result = await self._request_data("GET", "/maimaidxplate")
        return result.content
    
    async def get_alias(self) -> dict[str, str | int | list[str]]:
        """获取所有别名"""
        result = await self._request_data("GET", "/maimaidxalias")
        return result.content

    async def get_songs(self, name: str) -> list[Alias]:
        """
        使用别名查询曲目。
        `code` 为 `0` 时返回值为 `List[Alias]`。
        `code` 为 `3006` 时返回值为 `List[AliasStatus]`。
        
        Params:
            `name`: 别名
        Returns:
            `Union[List[AliasStatus], List[Alias]]`
        """
        result = await self._request_data("GET", "/getsongs", params={"name": name})
        if result.code == 3006:
            return []
        elif result.code == 1004:
            return []
        elif result.code == 0:
            return [Alias.model_validate(s) for s in result.content]
        else:
            raise UnknownError

    async def get_songs_alias(self, song_id: int) -> Alias | str:
        """
        使用曲目 `id` 查询别名
        
        Params:
            `song_id`: 曲目 `ID`
        Returns:
            `Alias` | `str`
        """
        result = await self._request_data("GET", "/getsongsalias", params={"song_id": song_id})
        if result.code == 0:
            return Alias.model_validate(result.content)
        elif result.code == 1004:
            return result.content
        else:
            raise UnknownError