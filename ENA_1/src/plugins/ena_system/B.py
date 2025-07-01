# --------------------------
# 导入区域
# --------------------------
import random
import time
from typing import Dict, Tuple
from pathlib import Path
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent

from  ._430_ import check_group_whitelist, check_user_blacklist, check_authenticate_usage



# --------------------------
# 内存缓存
# --------------------------
# 内存缓存结构：{(group_id, user_id): (timestamp, nickname)}
# 缓存修正：单用户ID作为键
member_cache: Dict[Tuple[int, int], Tuple[float, str]] = {}  # {user_id: (timestamp, nickname)}
CACHE_EXPIRE = 3600  # 一小时缓存，可根据实际调整



# --------------------------
# 事件响应器
# --------------------------
authenticate_reply = on_fullmatch("鉴定")



# --------------------------
# 函数定义
# --------------------------
async def get_safe_nickname(bot: Bot, event: GroupMessageEvent) -> str:
    """安全获取QQ昵称的封装方法"""
    user_id = event.user_id
    group_id = event.group_id

    # cache_key = (user_id,)  # 修复元组表示方式

    # 方案1：完全移除群组维度（推荐，因QQ昵称全局唯一）
    # cache_key = user_id  # 直接使用user_id

    # 方案2：保留群组维度
    # cache_key = (group_id, user_id)  # 保持与定义一致

    cache_key = (group_id, user_id)    # 修正为(group_id, user_id)元组

    # 尝试读取缓存
    cache_data = member_cache.get(cache_key)

    if cache_data:
        cache_time, cached_name = cache_data
        if time.time() - cache_time < CACHE_EXPIRE:
            return cached_name
    else:
        cached_name = None  # 确保cached_name有默认值

    try:
        # 直接使用事件中的QQ昵称
        new_name = event.sender.nickname or "您"

        # 更新缓存（即使失败也保留旧缓存）
        member_cache[cache_key] = (time.time(), new_name)
        return new_name
    except Exception as e:
        # 失败时返回缓存值或默认值
        if cache_data:  # 如果之前有缓存数据
            return cached_name  # 现在cached_name总是有值
        return "您"



# --------------------------
# 事件处理
# --------------------------
@authenticate_reply.handle()
async def handle_reply(bot: Bot, event: GroupMessageEvent):
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await reply_tester.finish("本群未授权")
        return

    # 黑名单检查（紧接白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await reply_tester.finish(Message([
        #       MessageSegment.reply(event.message_id),
        #       MessageSegment.text("您已被禁用Ena-bot")
        #   ]))
        return

    # 获取用户id
    user_id = event.get_user_id()

    # 获取被回复消息的message_id
    # reply_msg_id = event.message_id

    # 检查使用限制
    if not (await check_authenticate_usage(user_id)):
        await authenticate_reply.finish(
            MessageSegment.reply(event.message_id) + "今天已经鉴定过了哦，明天再来吧"
        )

    try:
        group_nickname = await get_safe_nickname(bot, event)

        # 选取随机数
        random_num = random.randint(0, 1)
        
        # image_path = f"C:/QQbot/ENANA/src/plugins/authenticate/"
        image_path = Path(__file__).parent / f"resources/B/{random_num}.jpg"

        message = Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"ENA鉴定[{group_nickname}]为："),
            MessageSegment.image(file=image_path)
        ])

        await authenticate_reply.send(message)
    except Exception as e:
        await authenticate_reply.send(f"消息发送失败: {str(e)}")