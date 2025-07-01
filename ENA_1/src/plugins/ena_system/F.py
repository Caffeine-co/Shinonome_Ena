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
# 创建响应器，设置群聊、@机器人、正则匹配条件
chooser = on_regex(r"^(.+?)还是(.+?)$",rule=to_me())



# --------------------------
# 事件处理
# --------------------------
@chooser.handle()
async def handle_chooser(event: GroupMessageEvent):
    # 新增白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单检查（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await chooser.finish(Message([
        #       MessageSegment.reply(event.message_id),
        #       MessageSegment.text("您已被禁用Ena-bot")
        #   ]))
        return

    # 获取原始消息文本
    msg = event.get_plaintext().strip()
    
    # 使用正则匹配提取选项
    match = re.match(r"^(.+?)还是(.+?)$", msg)
    if not match:
        return
    
    # 提取两个选项并去除首尾空格
    option1 = match.group(1).strip()
    option2 = match.group(2).strip()
    option3 = "全都要"
    option4 = "都不要"

    # 随机选择结果
    result = random.choice([option1, option2, option3, option4])
    
    # 构建引用回复消息
    reply_msg = Message([
        MessageSegment.reply(event.message_id),  # 引用原消息
        MessageSegment.text(f"Ena建议你选择{result}")
    ])
    
    await chooser.finish(reply_msg)