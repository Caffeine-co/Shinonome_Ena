# --------------------------
# 导入区域
# --------------------------
from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment

from  ._430_ import check_group_whitelist, check_user_blacklist


# --------------------------
# 事件响应器
# --------------------------
calculate_power = on_startswith(("计算倍率", "倍率计算"))
calculate_together_score = on_startswith(("协力pt", "协力PT"))
calculate_solo_score = on_startswith(("单人pt", "单人PT"))
calculate_challenge_score = on_startswith(("挑战pt", "挑战PT"))


# --------------------------
# 事件处理
# --------------------------
@calculate_power.handle()
async def calculator_power_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    raw_msg = event.get_plaintext()

    args_part = raw_msg[len("计算倍率"):].strip()

    if not args_part:
        await calculate_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的卡呢，一张卡都没有吗")
        ]))

    args = args_part.split()
    if len(args) != 5:
        error_msg = (
            f"你怎么只拿得出来{len(args)}张卡" if len(args) < 5
            else "你的队伍倍率计算怎么超载了"
        )
        await calculate_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))

    try:
        a, b, c, d, e = map(float, args)
    except ValueError:
        await calculate_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的倍率怎么混进去奇怪的东西，瑞希教的？")
        ]))

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

    await calculate_power.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculate_together_score.handle()
async def calculator_together_score_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    raw_msg = event.get_plaintext()

    args_part = raw_msg[len("协力pt"):].strip()

    if not args_part:
        await calculate_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
                MessageSegment.text("你的参数呢，一个都没有吗")
        ]))

    args = args_part.split()

    if len(args) != 4:
        error_msg = (
            f"你怎么只输入了{len(args)}个参数" if len(args) < 4
            else "你的协力pt计算怎么超载了"
        )
        await calculate_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))

    try:
        a, c, d, e = map(float, args)
    except ValueError:
        await calculate_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    b = 1100000
    pt_score = round(((114+a/17500+b/100000)*c*(d/100+1))*e)

    result_msg = (
        f"🎮📊 协力模拟PT计算 📊🎮\n"
        f"• 活动协力pt: {pt_score}"
    )

    await calculate_together_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculate_solo_score.handle()
async def calculator_solo_score_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    raw_msg = event.get_plaintext()

    args_part = raw_msg[len("单人pt"):].strip()

    if not args_part:
        await calculate_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
                MessageSegment.text("你的参数呢，一个都没有吗")
        ]))

    args = args_part.split()

    if len(args) != 4:
        error_msg = (
            f"你怎么只输入了{len(args)}个参数" if len(args) < 4
            else "你的单人pt计算怎么超载了"
        )
        await calculate_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))

    try:
        a, b, c, d = map(float, args)
    except ValueError:
        await calculate_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    pt_score = round(((100+a/20000)*b*(c/100+1))*d)

    result_msg = (
        f"🎮📊 单人模拟PT计算 📊🎮\n"
        f"• 活动单人pt: {pt_score}"
    )

    await calculate_solo_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))


@calculate_challenge_score.handle()
async def calculator_challenge_score_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    raw_msg = event.get_plaintext()

    args_part = raw_msg[len("挑战pt"):].strip()

    if not args_part:
        await calculate_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数呢")
        ]))

    args = args_part.split()

    if len(args) > 1:
        error_msg = "你的挑战pt计算怎么超载了"

        await calculate_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))

    try:
        a = float(args[0])
    except ValueError:
        await calculate_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    pt_score = round((100+a/20000)*120)

    result_msg = (
        f"🎮📊 挑战模拟PT计算 📊🎮\n"
        f"• 活动挑战pt: {pt_score}"
    )

    await calculate_challenge_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))