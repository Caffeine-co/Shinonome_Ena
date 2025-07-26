# --------------------------
# 导入区域
# --------------------------
import random
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent

from ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one, time_restriction


# --------------------------
# 事件响应器
# --------------------------
draw_lots = on_regex(r"^(求签|抽签)\s+")


# --------------------------
# 事件处理
# --------------------------
@draw_lots.handle()
async def draw_lots_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_I", 2)):
        await draw_lots.finish(
            MessageSegment.reply(event.message_id) + "你今天已经求了两次签了，明天再来吧"
        )

    raw_msg = event.get_plaintext().strip()

    split_msg = raw_msg.split(maxsplit=1)

    if len(split_msg) < 2 or not split_msg[1].strip():
        await draw_lots.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的求签格式好像不太对呢")
        ]))

    content = split_msg[1].strip()

    fortune_dict = {
        1: ('大吉'),
        2: ('中吉'),
        3: ('末吉'),
        4: ('平'),
        5: ('亏'),
        6: ('小凶'),
        7: ('大凶')
    }

    random_num = random.randint(1, 7)
    title = fortune_dict[random_num]

    msg = Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text("🔮 灵签解析：\n"),
        MessageSegment.text(f"📝 求签内容：{content}\n"),
        MessageSegment.text(f"🎴 签文等级：{title}")
    ])

    await draw_lots.finish(msg)