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

AICHAT_WHITELIST_PATH = Path("C:/QQbot/ENA_1/src/plugins/ena_system/resources/use_limit/aichat_group_whitelist.db")

AICHAT_WHITELIST_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据库初始化
# --------------------------
async def init_aichat_group_whitelist_db():
    async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS aichat_group_whitelist (
                group_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
        ''')
        await db.commit()

@driver.on_startup
async def _():
    await init_aichat_group_whitelist_db()
    print("ai聊天白名单数据库初始化完成")


# --------------------------
# 消息响应器创建
# --------------------------
open_target_aichat = on_regex(r"^开启ai聊天\s*(\d+)$")
close_target_aichat = on_regex(r"^关闭ai聊天\s*(\d+)$")
query_target_aichat = on_regex(r"^查询ai聊天\s*(\d+)$")
open_current_aichat = on_fullmatch("开启ai聊天")
close_current_aichat = on_fullmatch("关闭ai聊天")
query_current_aichat = on_fullmatch(("查询ai聊天", "查ai聊天"))
query_aichat_group_list = on_fullmatch(("查询ai聊天群聊列表", "查ai聊天列表"))


# --------------------------
# 数据库操作函数
# --------------------------
async def get_aichat_whitelist() -> List[Dict[str, int]]:
    async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
        cursor = await db.execute("SELECT group_id, user_id FROM aichat_group_whitelist")
        rows = await cursor.fetchall()
        return [{"group_id": row[0], "user_id": row[1]} for row in rows]


async def get_group_info(group_id: int) -> Union[Dict[str, int], None]:
    async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
        cursor = await db.execute(
            "SELECT group_id, user_id FROM aichat_group_whitelist WHERE group_id = ?",
            (group_id,)
        )
        row = await cursor.fetchone()
        return {"group_id": row[0], "user_id": row[1]} if row else None


async def add_to_aichat_whitelist(group_id: int, user_id: int) -> str:
    try:
        async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM aichat_group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            if await cursor.fetchone():
                return "duplicate"

            await db.execute(
                "INSERT INTO aichat_group_whitelist (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id)
            )
            await db.commit()
            return "added"

    except Exception as e:
        print(f"添加白名单失败: group_id={group_id}, user_id={user_id}, error={str(e)}")
        return "error"


async def remove_from_aichat_whitelist(group_id: int) -> str:
    try:
        async with aiosqlite.connect(AICHAT_WHITELIST_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM aichat_group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            if not await cursor.fetchone():
                return "not_found"

            await db.execute(
                "DELETE FROM aichat_group_whitelist WHERE group_id = ?",
                (group_id,)
            )
            await db.commit()
            return "removed"

    except Exception as e:
        print(f"移除白名单失败: group_id={group_id}, error={str(e)}")
        return "error"


# --------------------------
# 开启目标群ai聊天事件处理
# --------------------------
@open_target_aichat.handle()
async def open_target_aichat_handler(
        bot: Bot,
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.user_id != admin_id:
        return

    group_id = int(args[0])

    user_id = event.user_id

    try:
        group_list = await bot.get_group_list()
        if group_id not in {g["group_id"] for g in group_list}:
            await open_target_aichat.finish(
                MessageSegment.reply(event.message_id) + f"🎨开启ai聊天失败啦，可能是ENA②未进入群聊 {group_id} 呢"
            )

    except MatcherException:
        raise

    except Exception as e:
        print(f"获取群列表失败: {str(e)}")
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨开启ai聊天失败啦，可能是系统错误，无法验证群聊存在性，请稍后再试呢"
        )

    result = await add_to_aichat_whitelist(group_id, user_id)

    if result == "added":
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 开启ai聊天成功啦！\n🎨操作人：{user_id}"
        )

    elif result == "duplicate":
        entry = await get_group_info(group_id)

        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨这个群已经开启了ai聊天啦！\n🎨操作人：{entry['user_id'] if entry else '未知'}"
        )

    elif result == "error":
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨开启ai聊天失败啦，可能是数据库操作出错呢"
        )

    else:
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨开启ai聊天失败啦，请检查群号格式或联系开发者呢"
        )


# --------------------------
# 开启当前群ai聊天事件处理
# --------------------------
@open_current_aichat.handle()
async def open_target_aichat_handler(
        event: GroupMessageEvent
):
    if event.user_id != admin_id:
        return

    group_id = event.group_id
    user_id = event.user_id

    result = await add_to_aichat_whitelist(group_id, user_id)

    if result == "added":
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 开启ai聊天成功啦！\n🎨操作人：{user_id}"
        )

    elif result == "duplicate":
        entry = await get_group_info(group_id)

        await open_target_aichat.finish(
            MessageSegment.reply(
                event.message_id) + f"🎨这个群已经开启了ai聊天啦！\n🎨操作人：{entry['user_id'] if entry else '未知'}"
        )

    elif result == "error":
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨开启ai聊天失败啦，可能是数据库操作出错呢"
        )

    else:
        await open_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨开启ai聊天失败啦，请检查群号格式或联系开发者呢"
        )


# --------------------------
# 关闭目标群ai聊天事件处理
# --------------------------
@close_target_aichat.handle()
async def close_target_aichat_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.user_id != admin_id:
        return

    group_id = int(args[0])

    result = await remove_from_aichat_whitelist(group_id)

    if result == "removed":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨已关闭群聊 {group_id} 的ai聊天"
        )

    elif result == "not_found":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 未开启过ai聊天"
        )

    elif result == "error":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨关闭ai聊天失败，数据库操作出错"
        )

    else:
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨关闭ai聊天失败，未知错误"
        )


# --------------------------
# 关闭当前群ai聊天事件处理
# --------------------------
@close_current_aichat.handle()
async def close_target_aichat_handler(
        event: GroupMessageEvent
):
    if event.user_id != admin_id:
        return

    group_id = event.group_id

    result = await remove_from_aichat_whitelist(group_id)

    if result == "removed":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨已关闭群聊 {group_id} 的ai聊天"
        )

    elif result == "not_found":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {group_id} 未开启过ai聊天"
        )

    elif result == "error":
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨关闭ai聊天失败，数据库操作出错"
        )

    else:
        await close_target_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨关闭ai聊天失败，未知错误"
        )


# --------------------------
# 查询指定群ai聊天事件处理
# --------------------------
@query_target_aichat.handle()
async def query_target_aichat_handler(
        event: GroupMessageEvent,
        args: Tuple[str, ...] = RegexGroup()
):
    if event.group_id != auth_group:
        return

    target_group = int(args[0])

    entry = await get_group_info(target_group)

    if entry:
        await query_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {target_group} 已开启ai聊天\n🎨操作人：{entry['user_id']}"
        )

    elif entry is None:
        await query_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨群聊 {target_group} 未开启ai聊天"
        )

    else:
        await query_target_aichat.finish(
            MessageSegment.reply(event.message_id) + f"🎨查询群聊 {target_group} 的ai聊天信息失败，数据库错误，请稍后再试"
        )


# --------------------------
# 查询当前群ai聊天事件处理
# --------------------------
@query_current_aichat.handle()
async def query_current_aichat_handler(
        event: GroupMessageEvent
):
    current_group = event.group_id

    entry = await get_group_info(current_group)

    if entry:
        await query_current_aichat.finish(
                MessageSegment.reply(event.message_id) + f"🎨本群已开启ai聊天\n🎨操作人：{entry['user_id']}"
            )

    elif entry is None:
        await query_current_aichat.finish(
                MessageSegment.reply(event.message_id) + f"🎨本群未开启ai聊天"
            )

    else:
        await query_current_aichat.finish(
            MessageSegment.reply(event.message_id) + "🎨查询本群的ai聊天信息失败，数据库错误，请稍后再试"
        )


# --------------------------
# 查询已开启ai聊天群聊列表
# --------------------------
@query_aichat_group_list.handle()
async def query_aichat_group_list_handler(
        event: GroupMessageEvent
):
    if event.user_id != admin_id:
        return

    try:
        whitelist = await get_aichat_whitelist()
        if not whitelist:
            await query_aichat_group_list.finish(
                MessageSegment.reply(event.message_id) + "🎨当前没有已开启ai聊天的群聊哦"
            )

        group_list = "🎨群号列表：\n" + "，\n".join(
            [str(entry["group_id"]) for entry in whitelist]
        )

        group_list += f"\n\n🎨共 {len(whitelist)} 个群聊已开启ai聊天"

        await query_aichat_group_list.finish(
            MessageSegment.reply(event.message_id) + group_list
        )

    except MatcherException:
        raise

    except Exception as e:
        print(f"查询授权列表失败: {str(e)}")
        await query_aichat_group_list.finish(
            MessageSegment.reply(event.message_id) + "🎨查询ai聊天群聊列表失败，请稍后重试或查看日志信息"
        )