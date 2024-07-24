from pathlib import Path
from typing import Union

from nonebot.adapters.qq import AtMessageCreateEvent, GroupAtMessageCreateEvent
from nonebot.adapters.qq import MessageSegment as QM
from nonebot.adapters.qq.message import Attachment, LocalAttachment

from .config import FileServer
from .libraries.image import Image, image_to_bytesio, image_to_save


class MessageSegment(QM):
    
    async def image(event: Union[AtMessageCreateEvent, GroupAtMessageCreateEvent], data: Union[str, Path, Image.Image]) -> Union[LocalAttachment, Attachment]:
        if isinstance(event, AtMessageCreateEvent):
            if isinstance(data, Image.Image):
                data = image_to_bytesio(data)
            return QM.file_image(data)
        else:
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