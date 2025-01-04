from pathlib import Path
from typing import Optional, Union

from loguru import logger
from nonebot.adapters.qq import AtMessageCreateEvent, GroupAtMessageCreateEvent, Message
from nonebot.adapters.qq import MessageSegment as QM
from nonebot.adapters.qq.exception import ActionFailed
from nonebot.adapters.qq.message import Attachment, LocalAttachment
from nonebot.matcher import Matcher

from .config import FileServer
from .libraries.image import Image, image_to_bytesio, image_to_save


async def image(
    event: Union[AtMessageCreateEvent, GroupAtMessageCreateEvent], 
    data: Union[str, Path, Image.Image]
) -> Union[Attachment, LocalAttachment]:
    if isinstance(event, AtMessageCreateEvent):
        if isinstance(data, Image.Image):
            data = image_to_bytesio(data)
            return QM.file_image(data)

    if isinstance(data, Image.Image):
        file = await image_to_save(data)
    elif isinstance(data, Path):
        _p = data.as_posix().split('/')
        if 'maimaidxhelp.png' in _p:
            file = FileServer + f'/help/{_p[-1]}'
        elif 'rating' in _p:
            file = FileServer + f'/rating/{_p[-1]}'
        elif 'cover' in _p:
            file = FileServer + f'/cover/{_p[-1]}'
    return QM.image(file)


async def send_image(
    matcher: Matcher, 
    msg: Optional[Message] = None,
    event: Optional[Union[AtMessageCreateEvent, GroupAtMessageCreateEvent]] = None, 
    data: Optional[Union[str, Path, Image.Image]] = None
) -> None:
    if event is not None and data is not None:
        msg = await image(event, data)
    for n in range(3):
        try:
            await matcher.finish(msg)
        except ActionFailed as e:
            logger.error(f'{e}: 发送失败，正在重新发送')
            continue