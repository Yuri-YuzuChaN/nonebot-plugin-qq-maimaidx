from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
)
from nonebot.matcher import Matcher

from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user


async def get_user_db(
    matcher: Matcher,
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent | DirectMessageCreateEvent
) -> User:
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            open_id = event.author.member_openid
        else:
            open_id = event.author.id
        return await get_user(open_id)
    except UserNotBindError:
        await matcher.finish("您尚未绑定Bot，请输入「/绑定 qq号」进行绑定")