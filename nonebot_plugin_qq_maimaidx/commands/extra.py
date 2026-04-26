from nonebot.adapters.qq import AtMessageCreateEvent, GroupAtMessageCreateEvent
from nonebot.matcher import Matcher

from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user, update_user


async def get_optional_user(
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent
) -> User | None:
    try:
        if isinstance(event, GroupAtMessageCreateEvent):
            open_id = event.author.member_openid
        else:
            open_id = event.author.id
        return await get_user(open_id)
    except UserNotBindError:
        return None


async def get_user_db(
    matcher: Matcher,
    event: GroupAtMessageCreateEvent | AtMessageCreateEvent
) -> User:
    if isinstance(event, GroupAtMessageCreateEvent):
        open_id = event.author.member_openid
    else:
        open_id = event.author.id
    try:
        return await get_user(open_id)
    except UserNotBindError:
        await update_user(open_id)
        await matcher.finish(
            (
                "您尚未绑定Bot。\n"
                "可使用「/绑定 QQ号」进行绑定，绑定后即可查询水鱼查分器。\n"
                "绑定QQ号后，可使用「/绑定落雪」绑定落雪查分器。"
            )
        )