import re

from nonebot.adapters.qq import (
    AtMessageCreateEvent,
    DirectMessageCreateEvent,
    GroupAtMessageCreateEvent,
    GroupMessageCreateEvent,
    Message,
)
from nonebot.consts import CMD_ARG_KEY, PREFIX_KEY, REGEX_MATCHED
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.typing import T_State

from ..config import maiconfig
from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user, update_user
from ..core.merge.models import ServiceName, Song
from ..core.service import mai

AUTHORIZE_ERROR = (
    f"您尚未授权「{maiconfig.bot_name} BOT」"
    "访问您的落雪查分器数据，请先使用「/绑定落雪」指令进行绑定。"
)


class UniCommand:
    def __init__(self, *, regex_group: int | str | tuple[int | str, ...] = 1):
        """
        获取命令参数或正则匹配内容

        Params:
            `regex_group`: 正则触发时返回的捕获组，默认为第 1 组；传入元组时
                会用空格拼接多个非空捕获组
        """
        self.regex_group = regex_group

    def __call__(self, state: T_State) -> str:
        match: re.Match[str] | None = state.get(REGEX_MATCHED)
        if match:
            if isinstance(self.regex_group, tuple):
                return " ".join(
                    value.strip()
                    for group in self.regex_group
                    if (value := match.group(group)) is not None and value.strip()
                )
            value = match.group(self.regex_group)
            return value.strip() if value is not None else ""

        message: Message | None = state.get(PREFIX_KEY, {}).get(CMD_ARG_KEY)
        if message is not None:
            return message.extract_plain_text().strip()

        return ""


class GetUserModel:
    def __init__(
        self,
        auto_create: bool = True,
        check_auth: bool = False,
        check_skip: bool = False,
    ):
        """
        用户绑定依赖注入类

        Params:
            `auto_create`: 自动创建用户数据
            `check_auth`: 是否检查落雪查分器 Token
            `check_skip`: 跳过是否存在用户检测
        """
        self.auto_create = auto_create
        self.check_auth = check_auth
        self.check_skip = check_skip

    async def __call__(
        self,
        matcher: Matcher,
        event: GroupAtMessageCreateEvent
        | GroupMessageCreateEvent
        | AtMessageCreateEvent
        | DirectMessageCreateEvent,
    ) -> User | None:
        if isinstance(event, GroupAtMessageCreateEvent):
            user_id = event.author.member_openid
        else:
            user_id = event.author.id

        user = None
        is_exist = False
        try:
            user = await get_user(user_id)
        except UserNotBindError:
            if self.auto_create:
                user = await update_user(user_id)

        qq_is_none = user.qqid is None

        if self.check_auth and user:
            if (
                user.service == ServiceName.LXNS
                and user.access_token is None
                and user.refresh_token is None
            ):
                if self.check_skip:
                    return None
                await matcher.finish(AUTHORIZE_ERROR, reply_message=True)
            if user.service == ServiceName.DIVINGFISH and qq_is_none:
                if self.check_skip:
                    return None
                await matcher.finish(
                    "请先使用「/绑定」指令绑定QQ。", reply_message=True
                )

            is_exist = True

        if self.check_skip:
            if not is_exist:
                return None

        return user


GetOrCreateUser = GetUserModel(auto_create=True)
"""获取用户数据，不检查授权，若不存在直接创建"""
GetUserOrNone = GetUserModel(auto_create=False, check_skip=True)
"""获取用户数据，若不存在则返回`None`，也不创建"""
GetUserAndAuth = GetUserModel(auto_create=True, check_auth=True)
"""获取用户数据，并检查是否授权，未授权则提示授权"""
GetUserAndAuthOrNone = GetUserModel(auto_create=True, check_auth=True, check_skip=True)
"""获取用户数据，若不存在则创建，并检查是否授权，未授权则返回`None`"""


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


async def process_regex(
    matcher: Matcher,
    raw_args: str = Depends(UniCommand(regex_group=(1, 2))),
) -> tuple[list[Song], int]:
    """
    查歌指令依赖注入函数，返回曲目列表以及页数

    Returns:
        `tuple[list[Song], int]`
    """
    match = re.search(r"^(定数|bpm|曲师|谱师)?\s?(.+)", raw_args, re.IGNORECASE)
    if not match:
        await matcher.finish("请输入要查询的乐曲信息", reply_message=True)
    raw_cmd = match.group(1)
    cmd = raw_cmd.lower() if raw_cmd is not None else None
    args = match.group(2)
    a_list = args.split() if args else []
    page = 1
    match cmd:
        case None:
            if not a_list:
                await matcher.finish(
                    "没有找到这样的乐曲。\n※ 如果是别名请使用「XXX是什么歌」指令进行查询哦。",
                    reply_message=True,
                )
            if len(a_list) >= 2 and a_list[-1].isdigit():
                title, page = " ".join(a_list[:-1]), int(a_list[-1])
            else:
                title = " ".join(a_list)
            result = mai.total_list.filter(title=title)
        case "定数":
            match a_list:
                case [ds] if is_float(ds):
                    ds1 = ds2 = float(ds)
                case [ds1_raw, ds2_raw] if is_float(ds1_raw) and is_float(ds2_raw):
                    ds1, ds2 = float(ds1_raw), float(ds2_raw)
                case [ds1_raw, ds2_raw, p_raw] if (
                    is_float(ds1_raw) and is_float(ds2_raw) and p_raw.isdigit()
                ):
                    ds1, ds2, page = float(ds1_raw), float(ds2_raw), int(p_raw)
                case _:
                    await matcher.finish(
                        (
                            "定数查歌参数错误，请输入正确格式，页数为可选：\n"
                            "定数查歌「定数」「页数」\n"
                            "定数查歌「最小定数」「最大定数」「页数」\n"
                        ),
                        reply_message=True,
                    )
            result = mai.total_list.filter(level_value=(ds1, ds2))
        case "bpm":
            match a_list:
                case [bpm_raw] if is_float(bpm_raw):
                    result = mai.total_list.filter(bpm=float(bpm_raw))
                case [b1, b2] if is_float(b1) and is_float(b2):
                    if float(b1) > float(b2):
                        page = int(float(b2))
                        result = mai.total_list.filter(bpm=float(b1))
                    else:
                        result = mai.total_list.filter(bpm=(float(b1), float(b2)))
                case [b1, b2, p_raw] if (
                    is_float(b1) and is_float(b2) and p_raw.isdigit()
                ):
                    result = mai.total_list.filter(bpm=(float(b1), float(b2)))
                    page = int(p_raw)
                case _:
                    await matcher.finish(
                        (
                            "bpm查歌参数错误，请输入正确格式，页数为可选：\n"
                            "bpm查歌「bpm」「页数」\n"
                            "bpm查歌「最小bpm」「最大bpm」「页数」\n"
                        ),
                        reply_message=True,
                    )
        case "曲师" | "谱师":
            if not a_list:
                await matcher.finish(
                    (
                        f"{cmd}查歌参数错误，请输入正确格式，页数为可选：\n"
                        f"{cmd}查歌「{cmd}」「页数」"
                    ),
                    reply_message=True,
                )
            if len(a_list) >= 2 and a_list[-1].isdigit():
                name, page = " ".join(a_list[:-1]), int(a_list[-1])
            else:
                name = " ".join(a_list)
            if cmd == "曲师":
                result = mai.total_list.filter(artist=name)
            else:
                result = mai.total_list.filter(charter=name, all_diff=False)
        case _:
            await matcher.finish("指令错误", reply_message=True)

    return result, page
