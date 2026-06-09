from nonebot.adapters.qq import MessageSegment as QQMessageSegment

from .image.tools import base64_to_bytesio


class MessageSegment(QQMessageSegment):
    @staticmethod
    def image(data: str) -> QQMessageSegment:
        return QQMessageSegment.file_image(base64_to_bytesio(data))
