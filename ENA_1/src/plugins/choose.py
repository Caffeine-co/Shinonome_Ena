import aiofiles
import json
import random
import re
from pathlib import Path
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment, Message
from nonebot.plugin import on_regex
from nonebot.rule import to_me

WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"

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

chooser = on_regex(r"^(.+?)还是(.+?)$",rule=to_me())

@chooser.handle()
async def handle_chooser(event: GroupMessageEvent):
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
    
    await chooser.finish(reply_msg)