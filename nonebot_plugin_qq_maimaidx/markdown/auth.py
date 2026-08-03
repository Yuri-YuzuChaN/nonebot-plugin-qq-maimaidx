from nonebot.adapters.qq import MessageSegment
from nonebot.adapters.qq.models import (
    Action,
    Button,
    InlineKeyboard,
    InlineKeyboardRow,
    MessageKeyboard,
    Permission,
    RenderData,
)

from ..config import lxnsconfig, maiconfig

AUTHORIZE_URL = (
    "https://maimai.lxns.net/oauth/authorize"
    "?response_type=code"
    f"&client_id={lxnsconfig.lx_client_id}"
    f"&redirect_uri={lxnsconfig.redirect_uri}"
    f"&scope=read_player+read_user_profile+write_player"
)

auth_button = [
    Button(
        id="1",
        render_data=RenderData(
            label="落雪查分器授权页",
            visited_label="落雪查分器授权页",
            style=1,
        ),
        action=Action(
            type=0,
            permission=Permission(type=2),
            data=AUTHORIZE_URL,
        ),
    )
]

auth_keyboard = MessageSegment.keyboard(
    MessageKeyboard(
        content=InlineKeyboard(rows=[InlineKeyboardRow(buttons=auth_button)]),
    )
)

auth_md = (
    MessageSegment.markdown(
        "**授权访问数据**\n"
        "请点击「落雪查分器授权页」获取授权码，"
        f"允许「{maiconfig.bot_name} BOT」访问您的落雪查分器数据"
        "\n=======================\n"
        "您应收到该格式的授权码："
        "`「XXXX-XXXX-XXXX」`\n"
        "请复制该授权码，并粘贴并发送到该窗口完成授权"
        "\n=======================\n"
        "请注意！！您必须在落雪查分器的"
        "「账号设置 -> 常规设置 -> 隐私设置」"
        "开启允许读取成绩，否则BOT将无法查询您的成绩"
    )
    + auth_keyboard
)
