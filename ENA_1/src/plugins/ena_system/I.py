# --------------------------
# 导入区域
# --------------------------
import random
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent

from ._430_ import check_group_whitelist, check_user_blacklist, check_draw_lots_usage



# --------------------------
# 事件响应器
# --------------------------
# 严格匹配指令格式：以"求签"或"抽签"开头，后跟至少一个空格
lots_drawing = on_regex(r"^(求签|抽签)\s+")



# --------------------------
# 事件处理
# --------------------------
@lots_drawing.handle()
async def send_msg(event: GroupMessageEvent):
    # 白名单验证（新增核心逻辑）
    if not await check_group_whitelist(event.group_id):
        # await lots_drawing.finish(Message([
        #    MessageSegment.reply(event.message_id),
        #    MessageSegment.text("❌ 该群未获得求签权限，请联系管理员授权")
        # ]))
        return

    # 黑名单验证（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await lots_drawing.finish(Message([
        #       MessageSegment.reply(event.message_id),
        #       MessageSegment.text("您已被禁用Ena-bot")
        #   ]))
        return

    user_id = event.get_user_id()

    # 检查使用限制
    if not (await check_draw_lots_usage(user_id)):
        await lots_drawing.finish(
            MessageSegment.reply(event.message_id) + "你今天已经求了三次签了，明天再来吧"
        )

    # 获取原始消息并去除首尾空格
    raw_msg = event.get_plaintext().strip()

    # 分割指令和内容（至少分割1次）
    split_msg = raw_msg.split(maxsplit=1)

    # 校验内容有效性
    if len(split_msg) < 2 or not split_msg[1].strip():
        # 引用原消息的格式错误提示
        await lots_drawing.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的求签格式好像不太对呢")
        ]))

    content = split_msg[1].strip()  # 提取有效内容

    # 签文结果字典
    fortune_dict = {
        1: ('大吉'),
        2: ('中吉'),
        3: ('末吉'),
        4: ('平'),
        5: ('亏'),
        6: ('小凶'),
        7: ('大凶')
    }

    # 生成结果
    random_num = random.randint(1, 7)
    title = fortune_dict[random_num]

    # 构建消息
    msg = Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text("🔮 灵签解析：\n"),
        MessageSegment.text(f"📝 求签内容：{content}\n"),
        MessageSegment.text(f"🎴 签文等级：{title}")
    ])

    await lots_drawing.finish(msg)