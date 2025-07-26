# --------------------------
# 导入区域
# --------------------------
import random
import re
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, Message
from nonebot.plugin import on_regex

from ._430_ import check_group_whitelist, check_user_blacklist, time_restriction

# --------------------------
# 事件响应器
# --------------------------
choose = on_regex(r"^\s*(.+?)\s*还是\s*(.+?)(?:\s*还是\s*.+)*\s*$")


# --------------------------
# 事件处理
# --------------------------
@choose.handle()
async def choose_handler(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    at_id = re.findall("[0-9]{5,11}", event.raw_message)
    if len(at_id) == 0:
        return
    at_id = at_id[0]
    if at_id != bot.self_id:
        return

    if await time_restriction():
        return

    option = [opt.strip() for opt in event.get_plaintext().split("还是") if opt.strip()]

    if len(option) < 2:
        return

    option.append("全都要")
    option.append("都不要")

    result = random.choice(option)

    # 构建引用回复消息
    reply_msg = Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(f"Ena建议你选择{result}")
    ])

    await choose.finish(reply_msg)