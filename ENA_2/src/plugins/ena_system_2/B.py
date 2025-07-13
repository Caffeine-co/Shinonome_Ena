from pathlib import Path
import aiosqlite
from nonebot import get_driver, on_regex
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.params import RegexGroup
from nonebot.plugin.on import on_fullmatch

# --------------------------
# 路径与配置初始化
# --------------------------
driver = get_driver()
global_config = driver.config
admin_id = int(global_config.admin_id)
auth_group = int(global_config.auth_group)

BLACKLIST_PATH = Path("C:/QQbot/ENA_1/src/plugins/ena_system/resources/use_limit/user_blacklist.db")

BLACKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据库初始化函数
# --------------------------
async def init_user_blacklist_db():
    async with aiosqlite.connect(BLACKLIST_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_blacklist (
                user_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

@driver.on_startup
async def _():
    await init_user_blacklist_db()
    print("黑名单数据库初始化完成")


# --------------------------
# 消息响应器创建
# --------------------------
add_blacklist = on_regex(r"^拉黑用户\s*(\d+)$")
del_blacklist = on_regex(r"^解除用户\s*(\d+)$")
query_blacklist_list = on_fullmatch(("查询黑名单列表", "查黑名单列表"))
query_blacklist_user = on_regex(r"^查询黑名单\s*(\d+)$")


# --------------------------
# 数据库操作函数
# --------------------------
async def update_blacklist(user_id: int, operation: str) -> str:
    try:
        async with aiosqlite.connect(BLACKLIST_PATH) as db:
            if operation == "add":
                cursor = await db.execute(
                    "SELECT 1 FROM user_blacklist WHERE user_id = ?",
                    (user_id,)
                )
                exists = await cursor.fetchone()

                if exists:
                    return "duplicate"

                await db.execute(
                    "INSERT INTO user_blacklist (user_id) VALUES (?)",
                    (user_id,)
                )
                await db.commit()
                return "added"

            elif operation == "remove":
                cursor = await db.execute(
                    "SELECT 1 FROM user_blacklist WHERE user_id = ?",
                    (user_id,)
                )
                exists = await cursor.fetchone()

                if not exists:
                    return "not_found"

                await db.execute(
                    "DELETE FROM user_blacklist WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                return "removed"

    except Exception as e:
        print(f"黑名单操作失败: {str(e)}")
        return "error"

async def get_blacklist() -> list:
    try:
        async with aiosqlite.connect(BLACKLIST_PATH) as db:
            async with db.execute("SELECT user_id FROM user_blacklist") as cursor:
                return [row[0] async for row in cursor]
    except Exception as e:
        print(f"读取黑名单失败: {str(e)}")
        return []

async def check_blacklist(user_id: int) -> bool:
    try:
        async with aiosqlite.connect(BLACKLIST_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM user_blacklist WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                return bool(await cursor.fetchone())
    except Exception as e:
        print(f"查询用户黑名单状态失败: {str(e)}")
        return False


# --------------------------
# 添加黑名单事件处理
# --------------------------
@add_blacklist.handle()
async def add_blacklist_handler(
        event: GroupMessageEvent,
        matched: tuple = RegexGroup()
):
    if event.user_id != admin_id:
        return

    user_id = int(matched[0])

    result = await update_blacklist(user_id, "add")

    if result == "added":
        await add_blacklist.finish(
            MessageSegment.reply(event.message_id) + f"🎨ENA已拉黑用户 {user_id} ！\n🎨操作人：{event.user_id}"
        )
    elif result == "duplicate":
        await add_blacklist.finish(
            MessageSegment.reply(event.message_id) + f"🎨用户 {user_id} 已在ENA黑名单中，无需重复拉黑！"
        )
    else:
        await add_blacklist.finish(
            MessageSegment.reply(event.message_id) + "🎨黑名单添加失败，请检查格式或文件权限"
        )



# --------------------------
# 移除黑名单事件处理
# --------------------------
@del_blacklist.handle()
async def del_blacklist_handler(
        event: GroupMessageEvent,
        matched: tuple = RegexGroup()
):
    if event.user_id != admin_id:
        return

    user_id = int(matched[0])

    result = await update_blacklist(user_id, "remove")

    if result == "removed":
        await del_blacklist.finish(
            MessageSegment.reply(event.message_id) + f"🎨ENA已解除拉黑用户 {user_id} ！\n操作人：{event.user_id}"
        )
    elif result == "not_found":
        await del_blacklist.finish(
            MessageSegment.reply(event.message_id) + f"🎨用户 {user_id} 不在ENA黑名单中，无需解除拉黑！"
        )
    else:
        await del_blacklist.finish(
            MessageSegment.reply(event.message_id) + "🎨黑名单移除失败，请检查格式或文件权限"
        )


# --------------------------
# 查询单用户黑名单事件处理
# --------------------------
@query_blacklist_user.handle()
async def query_blacklist_user_handler(
        event: GroupMessageEvent,
        matched: tuple = RegexGroup()
):
    if event.group_id != auth_group:
        return

    user_id = int(matched[0])
    in_blacklist = await check_blacklist(user_id)

    result = f"🎨ENA{'已' if in_blacklist else '未'}拉黑用户 {user_id}"
    await query_blacklist_user.finish(
        MessageSegment.reply(event.message_id) + result
    )


# --------------------------
# 查询黑名单列表事件处理
# --------------------------
@query_blacklist_list.handle()
async def query_blacklist_list_handler(
        event: GroupMessageEvent
):
    if event.user_id != admin_id:
        return

    blacklist = await get_blacklist()
    count = len(blacklist)

    if count > 0:
        list_str = ""
        for user_id in blacklist:
            list_str += f"{user_id}，\n"

        list_str = list_str.rstrip("，\n")

        message = (
            f"🎨ENA黑名单列表：\n"
            f"{list_str}"
            f"\n\n共 {count} 人"
        )
    else:
        message = "🎨ENA黑名单列表为空"

    await query_blacklist_list.finish(
        MessageSegment.reply(event.message_id) + message
    )