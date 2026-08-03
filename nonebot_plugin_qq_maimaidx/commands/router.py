import re
from typing import Any

from nonebot import on_command as _on_command
from nonebot import on_regex as _on_regex
from nonebot.adapters import Message, MessageSegment
from nonebot.adapters.qq import MessageSegment as QQMessageSegment
from nonebot.matcher import Matcher, current_event


def _with_reply_message(
    message: str | Message | MessageSegment,
    reply_message: bool = False,
) -> str | Message | MessageSegment:
    if not reply_message:
        return message

    event = current_event.get()
    message_id = getattr(event, "id", None)
    if message_id is None:
        return message

    return QQMessageSegment.reference(message_id) + message


def _patch_reply_message(matcher: type[Matcher]) -> type[Matcher]:
    if getattr(matcher, "_reply_message_patched", False):
        return matcher

    send = matcher.send

    async def send_with_reply(
        cls: type[Matcher],
        message: str | Message | MessageSegment,
        *,
        reply_message: bool = False,
        **kwargs: Any,
    ) -> Any:
        return await send(
            _with_reply_message(message, reply_message=reply_message),
            **kwargs,
        )

    matcher.send = classmethod(send_with_reply)
    matcher._reply_message_patched = True
    return matcher


def on_command(*args: Any, **kwargs: Any) -> type[Matcher]:
    return _patch_reply_message(_on_command(*args, **kwargs))


def on_regex(
    pattern: str,
    flags: int | re.RegexFlag = 0,
    **kwargs: Any,
) -> type[Matcher]:
    return _patch_reply_message(_on_regex(pattern, flags=flags, **kwargs))
