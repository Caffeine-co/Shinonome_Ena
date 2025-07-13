from pathlib import Path
import aiosqlite
from nonebot import get_driver, on_regex, on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, ActionFailed
from nonebot.exception import MatcherException
from nonebot.params import RegexGroup
from typing import Tuple, Union, List, Dict


# --------------------------
# 路径与配置初始化
# --------------------------
driver = get_driver()
global_config = driver.config
admin_id = int(global_config.admin_id)
auth_group = int(global_config.auth_group)

WHITELIST_PATH = Path("C:/QQbot/ENA_1/src/plugins/ena_system/resources/use_limit/group_whitelist.db")

WHITELIST_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据库初始化
# --------------------------
async def init_group_whitelist_db():
    async with aiosqlite.connect(WHITELIST_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS group_whitelist (
                group_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
        ''')
        await db.commit()

@driver.on_startup
async def _():
    await init_group_whitelist_db()
    print("白名单数据库初始化完成")


# --------------------------
# 消息响应器创建
# --------------------------
apply_auth = on_regex(r"^申请授权\s*(\d+)$")
cancel_target_auth = on_regex(r"^取消授权\s*(\d+)$")
cancel_current_auth = on_fullmatch("取消授权")
change_user = on_regex(r"^更换群聊\s*(\d+)\s*的领养人为\s*(\d+)$")
query_target_auth = on_regex(r"^查询授权\s*(\d+)$")
query_current_auth = on_fullmatch("查询授权")
query_by_admin = on_regex(r"^查询领养\s*(\d+)$")
query_by_user = on_fullmatch("查询领养")


# --------------------------
# 数据库操作函数
# --------------------------
async def get_whitelist() -> List[Dict[str, int]]:
    async with aiosqlite.connect(WHITELIST_PATH) as db:
        cursor = await db.execute("SELECT group_id, user_id FROM group_whitelist")
        rows = await cursor.fetchall()
        return [{"group_id": row[0], "user_id": row[1]} for row in rows]


async def get_group_info(group_id: int) -> Union[Dict[str, int], None]:
    async with aiosqlite.connect(WHITELIST_PATH) as db:
        cursor = await db.execute(
            "SELECT group_id, user_id FROM group_whitelist WHERE group_id = ?",
            (group_id,)
        )
        row = await cursor.fetchone()
        return {"group_id": row[0], "user_id": row[1]} if row else None


async def add_to_whitelist(group_id: int, user_id: int) -> str:
    try:
        async with aiosqlite.connect(WHITELIST_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            if await cursor.fetchone():
                return "duplicate"

            await db.execute(
                "INSERT INTO group_whitelist (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id)
            )
            await db.commit()
            return "added"

    except Exception as e:
        print(f"添加白名单失败: group_id={group_id}, user_id={user_id}, error={str(e)}")
        return "error"


async def remove_from_whitelist(group_id: int) -> str:
    try:
        async with aiosqlite.connect(WHITELIST_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            if not await cursor.fetchone():
                return "not_found"

            await db.execute(
                "DELETE FROM group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            await db.commit()
            return "removed"

    except Exception as e:
        print(f"移除白名单失败: group_id={group_id}, error={str(e)}")
        return "error"


async def update_group_owner(group_id: int, new_user_id: int) -> str:
    try:
        async with aiosqlite.connect(WHITELIST_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            if not await cursor.fetchone():
                return "not_found"

            await db.execute(
                "UPDATE group_whitelist SET user_id = ? WHERE group_id = ?",
                (new_user_id, group_id)
            )
            await db.commit()
            return "updated"

    except Exception as e:
        print(f"更新领养人失败: group_id={group_id}, new_user_id={new_user_id}, error={str(e)}")
        return "error"


async def get_groups_by_owner(user_id: int) -> List[int]:
    async with aiosqlite.connect(WHITELIST_PATH) as db:
        cursor = await db.execute(
            "SELECT group_id FROM group_whitelist WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


# --------------------------
# 申请授权事件处理
# --------------------------
@apply_auth.handle()
async def apply_auth_handler(
        bot: Bot,
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.group_id != auth_group:
        return

    group_id = int(args[0])

    user_id = event.user_id

    try:
        group_list = await bot.get_group_list()
        if group_id not in {g["group_id"] for g in group_list}:
            await apply_auth.finish(
                MessageSegment.reply(event.message_id) + f"🎨领养ENA失败啦，可能是ENA②未进入群聊 {group_id} 呢"
            )

    except MatcherException:
        raise

    except Exception as e:
        print(f"获取群列表失败: {str(e)}")
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，可能是系统错误，无法验证群聊存在性，请稍后再试呢"
        )

    try:
        member_info = await bot.get_group_member_info(
            group_id=group_id,
            user_id=user_id,
            no_cache=True
        )

        role = member_info.get("role", "")
        if role not in ["owner", "admin"]:
            await apply_auth.finish(
                MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，只有群主或管理员才能申请领养呢"
            )

    except ActionFailed as e:
        print(f"权限验证失败: {e}")
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，可能是权限验证失败了，请确保能获取成员信息呢"
        )

    except MatcherException:
        raise

    except Exception as e:
        print(f"权限验证异常: {e}")
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，可能是权限验证时发生未知错误呢"
        )

    result = await add_to_whitelist(group_id, user_id)

    if result == "added":
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 领养ENA成功啦！\n🎨领养人：{user_id}\n🎨领养人请不要退出本群和所授权的群哟~"
        )

    elif result == "duplicate":
        entry = await get_group_info(group_id)

        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨这个群已经领养过ENA啦！\n🎨领养人：{entry['user_id'] if entry else '未知'}\n🎨若需更换领养人请联系开发者呢"
        )

    elif result == "error":
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，可能是数据库操作出错呢"
        )

    else:
        await apply_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨领养ENA失败啦，请检查群号格式或联系开发者呢"
        )


# --------------------------
# 取消指定群授权事件处理
# --------------------------
@cancel_target_auth.handle()
async def cancel_auth_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.user_id != admin_id:
        return

    group_id = int(args[0])

    result = await remove_from_whitelist(group_id)

    if result == "removed":
        await cancel_target_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨已取消群聊 {group_id} 的ENA领养"
        )

    elif result == "not_found":
        await cancel_target_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 未领养过ENA"
        )

    elif result == "error":
        await cancel_target_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨取消授权失败，数据库操作出错"
        )

    else:
        await cancel_target_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨取消授权失败，未知错误"
        )


# --------------------------
# 取消当前群授权事件处理
# --------------------------
@cancel_current_auth.handle()
async def cancel_auth_handler(
        event: GroupMessageEvent
):
    if event.user_id != admin_id:
        return

    group_id = event.group_id

    result = await remove_from_whitelist(group_id)

    if result == "removed":
        await cancel_current_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨已取消群聊 {group_id} 的ENA领养"
        )

    elif result == "not_found":
        await cancel_current_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 未领养过ENA"
        )

    elif result == "error":
        await cancel_current_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨取消授权失败，数据库操作出错"
        )

    else:
        await cancel_current_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨取消授权失败，未知错误"
        )


# --------------------------
# 更换领养人事件处理
# --------------------------
@change_user.handle()
async def change_user_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.user_id != admin_id:
        return

    group_id, new_user_id = map(int, args[:2])

    result = await update_group_owner(group_id, new_user_id)

    if result == "updated":
        await change_user.finish(
            MessageSegment.reply(event.message_id) + f"🎨领养人更换成功啦！\n🎨群号：{group_id}\n🎨新领养人：{new_user_id}\n🎨请新领养人请不要退出本群和所授权的群哟~"
        )

    elif result == "not_found":
        await change_user.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 还没有领养ENA哦，无法更换领养人呢"
        )

    elif result == "error":
        await change_user.finish(
            MessageSegment.reply(event.message_id) + "🎨领养人更换失败啦，可能是数据库操作出错呢"
        )

    else:
        await change_user.finish(
            MessageSegment.reply(event.message_id) + "🎨领养人更换失败啦，可能是未知错误呢"
        )


# --------------------------
# 查询指定群授权事件处理
# --------------------------
@query_target_auth.handle()
async def query_target_auth_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.group_id != auth_group:
        return

    target_group = int(args[0])

    entry = await get_group_info(target_group)

    if entry:
        await query_target_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {target_group} 已授权领养Ena\n🎨领养人：{entry['user_id']}"
        )

    elif entry is None:
        await query_target_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {target_group} 未授权领养Ena"
        )

    else:
        await query_target_auth.finish(
            MessageSegment.reply(event.message_id) + f"🎨查询群聊 {target_group} 的授权信息失败，数据库错误，请稍后再试"
        )


# --------------------------
# 查询当前群授权事件处理
# --------------------------
@query_current_auth.handle()
async def query_current_auth_handler(
        event: GroupMessageEvent
):
    current_group = event.group_id
    entry = await get_group_info(current_group)

    if entry:
        await query_current_auth.finish(
                MessageSegment.reply(event.message_id) + f"🎨本群已授权领养Ena\n🎨领养人：{entry['user_id']}"
            )

    elif entry is None:
        await query_current_auth.finish(
                MessageSegment.reply(event.message_id) + f"🎨本群未授权领养Ena"
            )

    else:
        await query_current_auth.finish(
            MessageSegment.reply(event.message_id) + "🎨查询本群的授权信息失败，数据库错误，请稍后再试"
        )


# --------------------------
# 管理员查询领养人授权的群聊事件处理
# --------------------------
@query_by_admin.handle()
async def query_by_admin_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.user_id != admin_id:
        return

    user_id = int(args[0])

    group_ids = await get_groups_by_owner(user_id)
    group_count = len(group_ids)

    group_list_str = ""
    for gid in group_ids:
        group_list_str += f"{gid}，\n"

    if group_count > 0:
        message = (
            f"🎨领养人：{user_id} \n"
            f"🎨群聊个数： {group_count} \n"
            f"🎨群聊列表：\n{group_list_str}"
        )
        message = message.rstrip("，\n")
    else:
        message = (
            f"🎨领养人：{user_id} \n"
            f"🎨该领养人还没有过ENA呢"
        )

    await query_by_admin.finish(
        MessageSegment.reply(event.message_id) + message
    )


# --------------------------
# 领养人自查授权的群聊事件处理
# --------------------------
@query_by_user.handle()
async def query_by_user_handler(
        event: GroupMessageEvent
):
    user_id = event.user_id

    group_ids = await get_groups_by_owner(user_id)
    group_count = len(group_ids)

    group_list_str = ""
    for gid in group_ids:
        group_list_str += f"{gid}，\n"

    if group_count > 0:
        message = (
            f"🎨领养人：{user_id} \n"
            f"🎨群聊个数： {group_count} \n"
            f"🎨群聊列表：\n{group_list_str}"
        )
        message = message.rstrip("，\n")
    else:
        message = (
            f"🎨领养人：{user_id} \n"
            f"🎨您还没有过ENA呢"
        )

    await query_by_user.finish(
        MessageSegment.reply(event.message_id) + message
    )