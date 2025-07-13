# --------------------------
# 导入区域
# --------------------------
import json
import random
from pathlib import Path
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.params import RegexGroup
from typing import Tuple

from ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one


# --------------------------
# 配置区域
# --------------------------
config_path = Path(__file__).parent / "resources/C/blindbox_config.json"


# --------------------------
# 文件操作
# --------------------------
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)


# --------------------------
# 事件响应器
# --------------------------
draw_goods = on_regex(r"^抽一发(\S+)$")


# --------------------------
# 事件处理
# --------------------------
@draw_goods.handle()
async def draw_goods_handler(
        event: GroupMessageEvent,
        matched_groups: Tuple[str, ...] = RegexGroup()
):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    style = matched_groups[0].strip()

    if not style or style not in config:
        await draw_goods.finish(
            MessageSegment.reply(event.message_id) + "Ena没有收录这个款式捏"
        )

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_C", 3)):
        await draw_goods.finish(
            MessageSegment.reply(event.message_id) + "今天抽了很多了，明天再来吧"
        )

    style_config = config[style]
    max_num = style_config["max"]

    random_num = random.randint(1, max_num)

    character = None
    for key in sorted(map(int, style_config["characters"].keys())):
        if random_num <= key:
            character = style_config["characters"][str(key)]
            break

    if not character:
        return

    message = Message()
    message += MessageSegment.reply(event.message_id)
    message += MessageSegment.text(f"恭喜抽中[{character['name']}]哒~\n")
    message += MessageSegment.image(file=character["image"])

    await draw_goods.finish(message)