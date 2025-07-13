# --------------------------
# 导入区域
# --------------------------
import random
import time
from typing import Dict, Tuple
from pathlib import Path
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent
from nonebot.exception import MatcherException

from  ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one


# --------------------------
# 内存缓存
# --------------------------
member_cache: Dict[Tuple[int, int], Tuple[float, str]] = {}
CACHE_EXPIRE = 3600


# --------------------------
# 事件响应器
# --------------------------
authenticate = on_fullmatch("鉴定")


# --------------------------
# 函数定义
# --------------------------
async def get_safe_nickname(
        bot: Bot,
        event: GroupMessageEvent
) -> str:
    user_id = event.user_id
    group_id = event.group_id

    cache_key = (group_id, user_id)

    cache_data = member_cache.get(cache_key)

    if cache_data:
        cache_time, cached_name = cache_data
        if time.time() - cache_time < CACHE_EXPIRE:
            return cached_name
    else:
        cached_name = None

    try:
        new_name = event.sender.nickname or "您"

        member_cache[cache_key] = (time.time(), new_name)
        return new_name
    except Exception as e:
        if cache_data:
            return cached_name
        return "您"


# --------------------------
# 事件处理
# --------------------------
@authenticate.handle()
async def authenticate_handler(
        bot: Bot,
        event: GroupMessageEvent
):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_B", 1)):
        await authenticate.finish(
            MessageSegment.reply(event.message_id) + "今天已经鉴定过了哦，明天再来吧"
        )

    try:
        group_nickname = await get_safe_nickname(bot, event)

        random_num = random.randint(0, 1)

        image_path = Path(__file__).parent / f"resources/B/{random_num}.jpg"

        message = Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"ENA鉴定[{group_nickname}]为："),
            MessageSegment.image(file=image_path)
        ])

        await authenticate.finish(message)

    except MatcherException:
        raise

    except Exception as e:
        await authenticate.finish(f"消息发送失败: {str(e)}")