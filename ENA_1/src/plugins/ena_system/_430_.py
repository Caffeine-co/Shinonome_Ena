# --------------------------
# 导入区域
# --------------------------
import aiosqlite
import os
import re
import psutil
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from nonebot import require, get_bot


# --------------------------
# 配置区域
# --------------------------
WHITELIST_PATH = Path(__file__).parent / "resources/use_limit/group_whitelist.db"
AICHAT_WHITELIST_PATH = Path(__file__).parent / "resources/use_limit/aichat_group_whitelist.db"
BLACKLIST_PATH = Path(__file__).parent / "resources/use_limit/user_blacklist.db"

DATA_PATH = Path(__file__).parent / "resources/usage_data/usage_data.db"
GLOBAL_EXEMPT_USERS = [2083909754]


# --------------------------
# 黑白名单检查函数
# --------------------------
async def check_group_whitelist(group_id: int) -> bool:
    try:
        async with aiosqlite.connect(WHITELIST_PATH) as db:
            async with db.execute(
                    "SELECT 1 FROM group_whitelist WHERE group_id = ?",
                    (group_id,)
            ) as cursor:
                return bool(await cursor.fetchone())

    except aiosqlite.OperationalError as e:
        if "no such table" in str(e).lower() or "unable to open" in str(e).lower():
            return False
        return False

    except Exception as e:
        print(f"白名单核查异常: {str(e)}")
        return False


async def check_user_blacklist(user_id: int) -> bool:
    try:
        async with aiosqlite.connect(BLACKLIST_PATH) as db:
            async with db.execute(
                    "SELECT 1 FROM user_blacklist WHERE user_id = ?",
                    (user_id,)
            ) as cursor:
                return bool(await cursor.fetchone())

    except aiosqlite.OperationalError as e:
        if "no such table" in str(e).lower() or "unable to open" in str(e).lower():
            return False
        return True

    except Exception as e:
        print(f"白名单核查异常: {str(e)}")
        return True


async def check_ai_group_whitelist(group_id: int) -> bool:
    try:
        async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
            async with db.execute(
                    "SELECT 1 FROM aichat_group_whitelist WHERE group_id = ?",
                    (group_id,)
            ) as cursor:
                return bool(await cursor.fetchone())

    except aiosqlite.OperationalError as e:
        if "no such table" in str(e).lower() or "unable to open" in str(e).lower():
            return False
        return False

    except Exception as e:
        print(f"ai聊天白名单核查异常: {str(e)}")
        return False


# --------------------------
# 使用限制检查函数
# --------------------------
TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


async def init_db(table_names: list[str]):
    for name in table_names:
        if not TABLE_NAME_PATTERN.match(name):
            raise ValueError(f"Invalid table name: {name}")

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DATA_PATH) as db:
        for table_name in table_names:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} ("
                "user_id TEXT PRIMARY KEY, "
                "date TEXT NOT NULL, "
                "count INTEGER NOT NULL)"
            )
        await db.commit()


async def check_usage_one(
        user_id: int,
        table_name: str,
        max_daily_limit: int = 1,
        exempt_users: str | set[str] | None = None
) -> bool:
    if exempt_users is None:
        exempt_users = []

    if isinstance(exempt_users, str):
        exempt_users = [exempt_users]

    if user_id in GLOBAL_EXEMPT_USERS:
        print(f"用户 {user_id} 在全局豁免列表中，跳过限制检查")
        return True

    if user_id in exempt_users:
        print(f"用户 {user_id} 在插件级豁免列表中，跳过限制检查")
        return True

    if not TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    await init_db([table_name])

    current_date = datetime.now().strftime("%Y-%m-%d")
    new_count = 1
    over_limit = False

    async with aiosqlite.connect(DATA_PATH) as db:
        cursor = await db.execute(
            f"SELECT date, count FROM {table_name} WHERE user_id = ?",
            (user_id,)
        )
        record = await cursor.fetchone()

        if record:
            record_date, count = record
            if record_date == current_date:
                new_count = count + 1
                over_limit = new_count > max_daily_limit

        if not over_limit:
            await db.execute(
                f"INSERT INTO {table_name} (user_id, date, count) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET "
                "date = excluded.date, count = excluded.count",
                (user_id, current_date, new_count)
            )
            await db.commit()

    return not over_limit


async def check_usage_ten(
        user_id: int,
        table_name: str,
        max_daily_limit: int = 10,
        exempt_users: str | set[str] | None = None
) -> bool:
    if exempt_users is None:
        exempt_users = []

    if isinstance(exempt_users, str):
        exempt_users = [exempt_users]

    if user_id in GLOBAL_EXEMPT_USERS:
        print(f"用户 {user_id} 在全局豁免列表中，跳过限制检查")
        return True

    if user_id in exempt_users:
        print(f"用户 {user_id} 在插件级豁免列表中，跳过限制检查")
        return True

    if not TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    await init_db([table_name])

    current_date = datetime.now().strftime("%Y-%m-%d")
    new_count = 10
    over_limit = False

    async with aiosqlite.connect(DATA_PATH) as db:
        cursor = await db.execute(
            f"SELECT date, count FROM {table_name} WHERE user_id = ?",
            (user_id,)
        )
        record = await cursor.fetchone()

        if record:
            record_date, count = record
            if record_date == current_date:
                new_count = count + 10
                over_limit = new_count > max_daily_limit

        if not over_limit:
            await db.execute(
                f"INSERT INTO {table_name} (user_id, date, count) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET "
                "date = excluded.date, count = excluded.count",
                (user_id, current_date, new_count)
            )
            await db.commit()

    return not over_limit


# --------------------------
# 宵禁限制检查函数
# --------------------------
async def time_restriction() -> bool:
    time_periods = [
        (time(6, 30), time(23, 30)),
    ]

    timezone_offset = 8

    utc_now = datetime.now(timezone.utc)
    target_time = (utc_now + timedelta(hours=timezone_offset)).time()

    for start, end in time_periods:
        if start < end:
            if start <= target_time < end:
                return False
        else:
            if target_time >= start or target_time < end:
                return False

    return True


# --------------------------
# haruki连接定时任务
# --------------------------
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="6", minute="30", second="0", id="start")
async def up_and_run():
    print("SCHEDULER:start")
    try:
        os.startfile("C:/QQbot/HarukiBot/HarukiClient-Windows-x64-v1.1.7/HarukiClient-shortcut")
        msg = "大家早上好呢~"
    except Exception as e:
        msg = f"早上好，但是启动Haruki失败了。\n错误信息：{str(e)}"

    bot = get_bot()
    await bot.send_group_msg(group_id=728556872, message=msg)


@scheduler.scheduled_job("cron", hour="23", minute="30", second="0", id="end")
async def down_and_sleep():
    print("SCHEDULER:end")
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'HarukiClient-Windows-x64-v1.1.7.exe':
                print(f"找到进程: PID={proc.info['pid']}, 名称={proc.info['name']}")
                pid = proc.info['pid']
                proccess = psutil.Process(pid)
                proccess.terminate()
        msg = "大家晚安呢~"
    except Exception as e:
        msg = f"晚安，但是停止Haruki失败了。\n错误信息：{str(e)}"

    bot = get_bot()
    await bot.send_group_msg(group_id=728556872, message=msg)