import aiofiles
import json
import random
from datetime import datetime
from pathlib import Path
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.rule import startswith

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
            content = await f.read()
            blacklist = json.loads(content)
            return user_id in blacklist
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return True
    except Exception as e:
        return True

MAX_DAILY_LIMIT = 5
EXEMPT_USER_ID = "Your_own_qq_number"
DATA_FILE = Path(__file__).parent / "usage_data_blindgoods.json"

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

config_path = Path(__file__).parent / "blindbox_config.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

draw_handler = on_message(rule=startswith("抽一发"), block=False)


@draw_handler.handle()
async def handle_draw(event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return

    user_id = event.get_user_id()

    reply_msg_id = event.message_id
    
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    command = event.get_plaintext()
    if not command.startswith("抽一发"):
        return
    
    style = command[3:]
    if not style or style not in config:
        await draw_handler.finish(
            MessageSegment.reply(event.message_id) + "Ena没有收录这个款式捏"
        )

    if not (await check_usage(user_id)):
        await draw_handler.finish(
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

    await draw_handler.send(message)
