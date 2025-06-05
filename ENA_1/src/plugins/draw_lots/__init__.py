import aiofiles
import json
import random
from datetime import datetime
from pathlib import Path
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent
from nonebot.rule import regex

WHITELIST_PATH = Path("Your_bot_project_absolute_path/src/plugins/group_whitelist.json")
BLACKLIST_PATH = Path("Your_bot_project_absolute_path/src/plugins/user_blacklist.json")

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
    except Exception as e:
        return True

MAX_DAILY_LIMIT = 3
EXEMPT_USER_ID = "Your_own_qq_number"
DATA_FILE = Path(__file__).parent / "usage_data_draw_lots.json"

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

catch_str = on_message(rule=regex(r"^(求签|抽签)\s+"))


@catch_str.handle()
async def send_msg(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        await catch_str.finish()
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.get_user_id()
    
    if not (await check_usage(user_id)):
        await catch_str.finish(
            MessageSegment.reply(event.message_id) + "你今天已经求了三次签了，明天再来吧"
        )

    raw_msg = event.get_plaintext().strip()

    split_msg = raw_msg.split(maxsplit=1)

    if len(split_msg) < 2 or not split_msg[1].strip():
        await catch_str.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的求签格式好像不太对呢")
        ]))
        return

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

    await catch_str.finish(msg)