# --------------------------
# 导入区域
# --------------------------
import aiofiles
import asyncio
import json
import random
import nonebot
from aiofiles import os as aio_os
from datetime import datetime, timedelta
from pathlib import Path
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent

from  ._430_ import check_group_whitelist, check_user_blacklist



# --------------------------
# 配置区域
# --------------------------
# 创建存储目录
# DATA_PATH = Path("data/sign")
# DATA_PATH.mkdir(parents=True, exist_ok=True)
DATA_FILE = Path(__file__).parent / "resources/G/user_sign_data.json"



# --------------------------
# 文件操作
# --------------------------
# 文件锁防止并发冲突
file_lock = asyncio.Lock()


# 读取用户数据（无锁，用于查询）
async def read_user_data() -> dict:
    """读取用户数据，不获取锁，适合只读操作"""
    if not await aio_os.path.exists(DATA_FILE):
        return {}

    async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content) if content else {}


# 读写用户数据（带锁，用于签到）
async def write_user_data(user_id: str, update_func) -> dict:
    """读写用户数据，获取文件锁防止并发冲突

    Args:
        user_id: 用户ID
        update_func: 更新用户数据的函数，接受用户数据字典作为参数
    """
    async with file_lock:  # 获取文件锁
        # 读取现有数据
        if await aio_os.path.exists(DATA_FILE):
            async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
                content = await f.read()
                user_data = json.loads(content) if content else {}
        else:
            user_data = {}

        # 初始化用户数据（如果不存在）
        if user_id not in user_data:
            user_data[user_id] = {
                "points": 0,
                "last_sign": "",
                "continuous_sign": 0
            }

        # 执行更新操作
        result = update_func(user_data[user_id])

        # 保存更新后的数据
        async with aiofiles.open(DATA_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(user_data, ensure_ascii=False, indent=2))

        return result



# --------------------------
# 函数定义
# --------------------------
# 计算用户等级
def calculate_level(points: int) -> int:
    return max(0, points // 50)  # 每50积分升一级，可更改


# 获取今日日期字符串
def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# 获取昨日日期字符串
def get_yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")



# --------------------------
# 事件响应器
# --------------------------
# 签到命令
sign_cmd = on_fullmatch("签到")

# 查询积分命令
query_cmd = on_fullmatch("我的芝士蛋糕")



# --------------------------
# 事件处理
# --------------------------
@sign_cmd.handle()
async def handle_sign(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = str(event.user_id)
    today = get_today()
    yesterday = get_yesterday()

    # 定义更新函数
    def update_user(user: dict) -> dict:
        # 检查今日是否已签到
        if user["last_sign"] == today:
            return {
                "status": "already_signed",
                "user": user
            }
        
        # 计算连续签到
        if user["last_sign"] == yesterday:
            # 连续签到，天数+1
            user["continuous_sign"] += 1
        else:
            # 非连续签到，重置为1
            user["continuous_sign"] = 1

        # 随机获取积分 (10-100)，可更改
        points_earned = random.randint(1, 10)
        user["points"] += points_earned
        user["last_sign"] = today
        # user["sign_days"] += 1

        return {
            "status": "success",
            "points_earned": points_earned,
            "user": user
        }

    # 执行带锁的更新操作
    result = await write_user_data(user_id, update_user)

    if result["status"] == "already_signed":
        # user = result["user"]
        # level = calculate_level(user["points"])

        msg = (
            f"你今天已经签到过啦"
            # f"你今天已经签到过啦\n"
            # f"🎨芝士蛋糕: {user['points']}块\n"
            # f"🎨绘画等级: Lv{level}"
        )

        await sign_cmd.finish(
            MessageSegment.reply(event.message_id) + msg
        )

    user = result["user"]
    points_earned = result["points_earned"]
    new_level = calculate_level(user["points"])

    # 构建回复消息
    msg = (
        f"签到成功！获得{points_earned}块芝士蛋糕\n"
        # f"• 累计签到: {user['sign_days']}天\n"
        f"🎨连续签到: {user['continuous_sign']}天\n"
        f"🎨芝士蛋糕: {user['points']}块\n"
        f"🎨绘画等级: Lv.{new_level}"
    )

    await sign_cmd.finish(
        MessageSegment.reply(event.message_id) + msg
    )


@query_cmd.handle()
async def handle_query(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = str(event.user_id)

    # 直接读取用户数据（无锁）
    user_data = await read_user_data()

    if user_id not in user_data or user_data[user_id]["points"] == 0:

        msg = "你还没有芝士蛋糕哦！使用[签到]获取芝士蛋糕吧"

        await query_cmd.finish(
            MessageSegment.reply(event.message_id) + msg
        )

    user = user_data[user_id]
    level = calculate_level(user["points"])
    last_sign = "从未签到" if not user["last_sign"] else user["last_sign"]

    msg = (
        # f"• 累计签到: {user['sign_days']}天\n"
        f"🎨连续签到: {user['continuous_sign']}天\n"
        f"🎨芝士蛋糕: {user['points']}块\n"
        f"🎨绘画等级: Lv.{level}\n"
        f"🎨最后签到: {last_sign}"
    )

    await query_cmd.finish(
        MessageSegment.reply(event.message_id) + msg
    )


# 初始化：确保数据文件存在
@nonebot.get_driver().on_startup
async def init_data():
    if not await aio_os.path.exists(DATA_FILE):
        async with aiofiles.open(DATA_FILE, "w", encoding="utf-8") as f:
            await f.write("{}")