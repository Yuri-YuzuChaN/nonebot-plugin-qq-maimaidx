from nonebot.adapters.qq.message import LocalAttachment, MessageSegment

from .image.chart import song_global_data
from .service import mai


async def draw_song_galobal_data(song_id: int, level_index: int) -> LocalAttachment:
    song = mai.total_list.by_id(song_id)
    image = await song_global_data(song, level_index)
    
    return MessageSegment.file_image(image)