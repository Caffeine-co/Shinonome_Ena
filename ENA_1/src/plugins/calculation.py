import aiofiles
import decimal
import json
from pathlib import Path
from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment

WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"

calculator_power = on_startswith(("计算倍率", "倍率计算"))
calculator_together_score = on_startswith(("协力pt", "协力PT", "计算pt", "计算PT", "pt计算", "PT计算"))
calculator_solo_score = on_startswith(("单人pt", "单人PT"))
calculator_challenge_score = on_startswith(("挑战pt", "挑战PT"))

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


@calculator_power.handle()
async def calculate_multiplier(event: GroupMessageEvent):
    raw_msg = event.get_plaintext()

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    args_part = raw_msg[len("计算倍率"):].strip()

    if not args_part:
        await calculator_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的卡呢，一张卡都没有吗")
        ]))
        return

    args = args_part.split()
    if len(args) != 5:
        error_msg = (
            f"你怎么只拿得出来{len(args)}张卡" if len(args) < 5
            else "你的队伍倍率计算怎么超载了"
        )
        await calculator_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))
        return

    try:
        a, b, c, d, e = map(float, args)
    except ValueError:
        await calculator_power.finish(Message([
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

    await calculator_power.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculator_together_score.handle()
async def calculate_multiplier(event: GroupMessageEvent):

    raw_msg = event.get_plaintext()

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    args_part = raw_msg[len("协力pt"):].strip()

    if not args_part:
        await calculator_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
                MessageSegment.text("你的参数呢，一个都没有吗")
        ]))
        return

    args = args_part.split()

    if len(args) != 4:
        error_msg = (
            f"你怎么只输入了{len(args)}个参数" if len(args) < 4
            else "你的协力pt计算怎么超载了"
        )
        await calculator_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))
        return

    try:
        a, c, d, e = map(float, args)
    except ValueError:
        await calculator_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))
        return

    b = 1100000
    pt_score = round(((114+a/17500+b/100000)*c*(d/100+1))*e)

    result_msg = (
        f"🎮📊 协力模拟PT计算 📊🎮\n"
        f"• 活动协力pt: {pt_score}"
    )

    await calculator_together_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculator_solo_score.handle()
async def calculate_multiplier(event: GroupMessageEvent):

    raw_msg = event.get_plaintext()

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    args_part = raw_msg[len("单人pt"):].strip()

    if not args_part:
        await calculator_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
                MessageSegment.text("你的参数呢，一个都没有吗")
        ]))
        return

    args = args_part.split()

    if len(args) != 4:
        error_msg = (
            f"你怎么只输入了{len(args)}个参数" if len(args) < 4
            else "你的单人pt计算怎么超载了"
        )
        await calculator_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))
        return

    try:
        a, b, c, d = map(float, args)
    except ValueError:
        await calculator_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))
        return

    pt_score = round(((100+a/20000)*b*(c/100+1))*d)

    result_msg = (
        f"🎮📊 单人模拟PT计算 📊🎮\n"
        f"• 活动单人pt: {pt_score}"
    )

    await calculator_solo_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculator_challenge_score.handle()
async def calculate_multiplier(event: GroupMessageEvent):
    raw_msg = event.get_plaintext()

    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    args_part = raw_msg[len("挑战pt"):].strip()

    if not args_part:
        await calculator_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数呢")
        ]))
        return

    args = args_part.split()

    if len(args) > 1:
        error_msg = "你的挑战pt计算怎么超载了"

        await calculator_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))
        return

    try:
        a = float(args[0])
    except ValueError:
        await calculator_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))
        return

    pt_score = round((100+a/20000)*120)

    result_msg = (
        f"🎮📊 挑战模拟PT计算 📊🎮\n"
        f"• 活动挑战pt: {pt_score}"
    )

    await calculator_challenge_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))