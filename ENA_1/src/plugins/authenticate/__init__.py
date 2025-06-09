import aiofiles
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent

WHITELIST_PATH = Path("***/ENA_1/src/plugins/group_whitelist.json")
BLACKLIST_PATH = Path("***/ENA_1/src/plugins/user_blacklist.json")

async def check_group_whitelist(group_id: int) -> bool:
    try:
        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            whitelist = json.loads(content)

            registered_groups = {entry["group_id"] for entry in whitelist}
            return group_id in registered_groups

    except (FileNotFoundError, json.JSONDecodeError):
        return False
    except KeyError:
        return False
    except Exception as e:
        print(f"白名单核查异常: {str(e)}")
        return False

async def check_user_blacklist(user_id: int) -> bool:
    try:
        async with aiofiles.open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            blacklist = json.loads(await f.read())
            return user_id in blacklist
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return True
    except Exception:
        return True

MAX_DAILY_LIMIT = 1
EXEMPT_USER_ID = "Your_qq_number"
DATA_FILE = Path(__file__).parent / "usage_data_authenticate.json"

async def check_usage(user_id: str):
    if user_id == EXEMPT_USER_ID:
        return True
    
    try:
        async with aiofiles.open(DATA_FILE, "r") as f:
            data = json.loads(await f.read())
    except FileNotFoundError:
        data = {}
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}
    
    if new_count > MAX_DAILY_LIMIT:
        return False
    
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE, "w") as f:
        await f.write(json.dumps(data, indent=2))
    
    return True

member_cache: Dict[Tuple[int, int], Tuple[float, str]] = {}
CACHE_EXPIRE = 3600

reply_tester = on_message(block=False)

async def get_safe_nickname(bot: Bot, event: GroupMessageEvent) -> str:
    user_id = event.user_id
    cache_key = (user_id,)

    if cache_data := member_cache.get(cache_key):
        cache_time, cached_name = cache_data
        if time.time() - cache_time < CACHE_EXPIRE:
            return cached_name

    try:
        new_name = event.sender.nickname or "您"

        member_cache[cache_key] = (time.time(), new_name)
        return new_name
    except Exception as e:
        return cached_name if cache_data else "您"


@reply_tester.handle()
async def handle_reply(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return

    if str(event.message) != "鉴定":
        return

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.get_user_id()

    reply_msg_id = event.message_id
    
    if not (await check_usage(user_id)):
        await reply_tester.finish(
            MessageSegment.reply(event.message_id) + "今天已经鉴定过了哦，明天再来吧"
        )

    random_num = random.randint(0, 1)

    try:
        group_nickname = await get_safe_nickname(bot, event)
        random_num = random.randint(0, 1)
        image_path = f"***/ENA_1/src/plugins/authenticate/{random_num}.jpg"

        message = Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"ENA鉴定[{group_nickname}]为："),
            MessageSegment.image(file=image_path)
        ])

        await reply_tester.send(message)
    except Exception as e:
        await reply_tester.send(f"消息发送失败: {str(e)}")