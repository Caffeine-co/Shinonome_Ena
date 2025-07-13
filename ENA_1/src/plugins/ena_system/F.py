# --------------------------
# 导入区域
# --------------------------
import random
import re
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment, Message
from nonebot.plugin import on_regex
from nonebot.rule import to_me

from  ._430_ import check_group_whitelist, check_user_blacklist


# --------------------------
# 事件响应器
# --------------------------
choose = on_regex(r"^(.+?)还是(.+?)$",rule=to_me())


# --------------------------
# 事件处理
# --------------------------
@choose.handle()
async def choose_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    msg = event.get_plaintext().strip()
    
    match = re.match(r"^(.+?)还是(.+?)$", msg)
    if not match:
        return
    
    option1 = match.group(1).strip()
    option2 = match.group(2).strip()
    option3 = "全都要"
    option4 = "都不要"

    result = random.choice([option1, option2, option3, option4])
    
    reply_msg = Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(f"Ena建议你选择{result}")
    ])
    
    await choose.finish(reply_msg)