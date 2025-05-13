import aiofiles
import decimal
import json
from pathlib import Path
from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.matcher import Matcher

WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"

matcher = on_message()

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

@matcher.handle()
async def calculate_multiplier(event: GroupMessageEvent, matcher: Matcher):
    raw_msg = event.get_plaintext()

    if not raw_msg.startswith("计算倍率"):
        return

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    args_part = raw_msg[len("计算倍率"):].strip()
    if not args_part:
        await matcher.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的卡呢，一张卡都没有吗")
        ]))
        return

    args = args_part.split()
    if len(args) != 5:
        error_msg = (
            f"你怎么只拿得出来{len(args)}张卡" if len(args) < 5
            else "你的队伍怎么超载了"
        )
        await matcher.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))
        return

    try:
        a, b, c, d, e = map(float, args)
    except ValueError:
        await matcher.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的倍率怎么混进去奇怪的东西，瑞希教的？")
        ]))
        return

    total = a + b + c + d + e
    avg_part = (b + c + d + e) / 5
    multiplier = (a + avg_part) / 100 + 1
    actual_value = a + avg_part

    result_msg = (
        f"🎮📊 模拟卡组分析 📊🎮\n"
        f"• 队长加成: {a}\n"
        f"• 综合加成: {total}\n"
        f"• 最终倍率: {multiplier:.2f}\n"
        f"• 技能效果值: {actual_value}%"
    )

    await matcher.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))