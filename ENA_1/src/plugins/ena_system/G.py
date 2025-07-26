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

from  ._430_ import check_group_whitelist, check_user_blacklist, time_restriction


# --------------------------
# 配置区域
# --------------------------
DATA_FILE = Path(__file__).parent / "resources/G/user_sign_data.json"


# --------------------------
# 文件操作
# --------------------------
file_lock = asyncio.Lock()


async def read_user_data() -> dict:
    if not await aio_os.path.exists(DATA_FILE):
        return {}

    async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content) if content else {}


async def write_user_data(user_id: str, update_func) -> dict:
    async with file_lock:
        if await aio_os.path.exists(DATA_FILE):
            async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
                content = await f.read()
                user_data = json.loads(content) if content else {}
        else:
            user_data = {}

        if user_id not in user_data:
            user_data[user_id] = {
                "points": 0,
                "last_sign": "",
                "continuous_sign": 0
            }

        result = update_func(user_data[user_id])

        async with aiofiles.open(DATA_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(user_data, ensure_ascii=False, indent=2))

        return result


# --------------------------
# 函数定义
# --------------------------
def calculate_level(points: int) -> int:
    return max(0, points // 50)


def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


# --------------------------
# 事件响应器
# --------------------------
sign = on_fullmatch("签到")
query_sign = on_fullmatch("我的芝士蛋糕")


# --------------------------
# 事件处理
# --------------------------
@sign.handle()
async def sign_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    user_id = str(event.user_id)
    today = get_today()
    yesterday = get_yesterday()

    def update_user(user: dict) -> dict:
        if user["last_sign"] == today:
            return {
                "status": "already_signed",
                "user": user
            }

        if user["last_sign"] == yesterday:
            user["continuous_sign"] += 1
        else:
            user["continuous_sign"] = 1

        points_earned = random.randint(1, 10)
        user["points"] += points_earned
        user["last_sign"] = today

        return {
            "status": "success",
            "points_earned": points_earned,
            "user": user
        }

    result = await write_user_data(user_id, update_user)

    if result["status"] == "already_signed":

        msg = (
            f"你今天已经签到过啦"
        )

        await sign.finish(
            MessageSegment.reply(event.message_id) + msg
        )

    user = result["user"]
    points_earned = result["points_earned"]
    new_level = calculate_level(user["points"])

    msg = (
        f"签到成功！获得{points_earned}块芝士蛋糕\n"
        f"🎨连续签到: {user['continuous_sign']}天\n"
        f"🎨芝士蛋糕: {user['points']}块\n"
        f"🎨绘画等级: Lv.{new_level}"
    )

    await sign.finish(
        MessageSegment.reply(event.message_id) + msg
    )


@query_sign.handle()
async def query_sign_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    user_id = str(event.user_id)

    user_data = await read_user_data()

    if user_id not in user_data or user_data[user_id]["points"] == 0:

        msg = "你还没有芝士蛋糕哦！使用[签到]获取芝士蛋糕吧"

        await query_sign.finish(
            MessageSegment.reply(event.message_id) + msg
        )

    user = user_data[user_id]
    level = calculate_level(user["points"])
    last_sign = "从未签到" if not user["last_sign"] else user["last_sign"]

    msg = (
        f"🎨连续签到: {user['continuous_sign']}天\n"
        f"🎨芝士蛋糕: {user['points']}块\n"
        f"🎨绘画等级: Lv.{level}\n"
        f"🎨最后签到: {last_sign}"
    )

    await query_sign.finish(
        MessageSegment.reply(event.message_id) + msg
    )


@nonebot.get_driver().on_startup
async def init_data():
    if not await aio_os.path.exists(DATA_FILE):
        async with aiofiles.open(DATA_FILE, "w", encoding="utf-8") as f:
            await f.write("{}")