# --------------------------
# 导入区域
# --------------------------
from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment

from  ._430_ import check_group_whitelist, check_user_blacklist



# --------------------------
# 事件响应器
# --------------------------
calculator_power = on_startswith(("计算倍率", "倍率计算"))
calculator_together_score = on_startswith(("协力pt", "协力PT", "计算pt", "计算PT", "pt计算", "PT计算"))
calculator_solo_score = on_startswith(("单人pt", "单人PT"))
calculator_challenge_score = on_startswith(("挑战pt", "挑战PT"))



# --------------------------
# 事件处理
# --------------------------
@calculator_power.handle()
async def calculate_multiplier(event: GroupMessageEvent):
    # 提取并处理消息内容
    raw_msg = event.get_plaintext()     # .strip()

    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await your_mather.finish("该群未授权")
        #   await matcher.finish(Message([
            #   MessageSegment.reply(event.message_id),
            #   MessageSegment.text("⛔ 该群未获得使用权限")
        #   ]))
        return

    # 黑名单检查（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await matcher.finish(Message([
        #       MessageSegment.reply(event.message_id),
        #       MessageSegment.text("您已被禁用Ena-bot")
        #   ]))
        return

    # 分割参数部分
    args_part = raw_msg[len("计算倍率"):].strip()

    if not args_part:
        await calculator_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的卡呢，一张卡都没有吗")       # ⚠️ 参数不能为空，请输入五个数值～
        ]))

    # 提取并验证参数数量
    # 优化参数提取逻辑（避免重复split）
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

    # 参数类型验证
    try:
        a, b, c, d, e = map(float, args)
    except ValueError:
        await calculator_power.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的倍率怎么混进去奇怪的东西，瑞希教的？")
        ]))

    # 核心计算逻辑
    total = a + b + c + d + e
    avg_part = (b + c + d + e) / 5  # 根据用户需求使用5除数
    multiplier = (a + avg_part) / 100 + 1
    actual_value = a + avg_part
    #   a、b、c、d、e对应队伍五张卡的技能加成

    # 构建格式化响应
    result_msg = (
        f"🎮📊 模拟卡组分析 📊🎮\n"
        f"• 队长加成: {a}\n"
        f"• 综合加成: {total}\n"
        f"• 最终倍率: {multiplier:.2f}\n"
        f"• 技能效果值: {actual_value}%"
    )

    # 发送带引用的群聊响应
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

    try:
        a, c, d, e = map(float, args)
    except ValueError:
        await calculator_together_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    b = 1100000
    pt_score = round(((114+a/17500+b/100000)*c*(d/100+1))*e)
    #   a：个人分数
    #   b：队友平均分数
    #   c：歌曲加成
    #   d：卡组加成
    #   e：消耗加成

    #   b = 13
    #   pt_score = round(((110+a/17000+b)*c*(d/100+1))*e)

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

    try:
        a, b, c, d = map(float, args)
    except ValueError:
        await calculator_solo_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    pt_score = round(((100+a/20000)*b*(c/100+1))*d)
    #   a：个人分数
    #   b：歌曲加成
    #   c：卡组加成
    #   d：消耗加成

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

    args = args_part.split()

    if len(args) > 1:
        error_msg = "你的挑战pt计算怎么超载了"

        await calculator_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(error_msg)
        ]))

    try:
        a = float(args[0])
    except ValueError:
        await calculator_challenge_score.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("你的参数怎么混进去奇怪的东西，瑞希教的？")
        ]))

    pt_score = round((100+a/20000)*120)
    #   a：个人分数

    result_msg = (
        f"🎮📊 挑战模拟PT计算 📊🎮\n"
        f"• 活动挑战pt: {pt_score}"
    )

    await calculator_challenge_score.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(result_msg)
    ]))