import json
import re
from pathlib import Path
from typing import Optional
import aiofiles
from nonebot import get_driver, on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import EventPlainText
from nonebot.permission import SUPERUSER

# 配置读取（需在.env文件添加配置）
global_config = get_driver().config
admin_id = int(global_config.admin_id)
auth_group = int(global_config.auth_group)

BLACKLIST_PATH = Path("Your_path/ENA_1/src/plugins/user_blacklist.json")

if not BLACKLIST_PATH.exists():
    BLACKLIST_PATH.write_text("[]", encoding='utf-8')

manager = on_message(block=True)
query_blacklist = on_regex(r"^查询黑名单\s*(\d+)?$")

async def update_blacklist(user_id: int, operation: str) -> bool:
    try:
        async with aiofiles.open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            blacklist = json.loads(content) if content else []

        if operation == "add":
            if user_id not in blacklist:
                blacklist.append(user_id)
        elif operation == "remove":
            if user_id in blacklist:
                blacklist.remove(user_id)

        async with aiofiles.open(BLACKLIST_PATH, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(blacklist, indent=4))
        return True
    except Exception as e:
        print(f"黑名单更新失败: {str(e)}")
        return False

async def get_blacklist() -> list:
    try:
        async with aiofiles.open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content else []
    except Exception as e:
        print(f"读取黑名单失败: {str(e)}")
        return []

@manager.handle()
async def handle_add(
    event: GroupMessageEvent,
    msg: str = EventPlainText()
):
    if str(event.user_id) != str(admin_id):
        return

    if match := re.match(r"^Enabladd\s*(\d+)$", msg.strip()):
        user_id = int(match.group(1))

        if await update_blacklist(user_id, "add"):
            await manager.finish(
                Message(f"用户 {user_id} 已被加入Ena黑名单！\n操作人：{event.user_id}")
            )
        else:
            await manager.finish("黑名单添加失败，请检查格式或文件权限")

@manager.handle()
async def handle_del(
    event: GroupMessageEvent,
    msg: str = EventPlainText()
):
    if str(event.user_id) != str(admin_id):
        return

    if match := re.match(r"^Enabldel\s*(\d+)$", msg.strip()):
        user_id = int(match.group(1))

        if await update_blacklist(user_id, "remove"):
            await manager.finish(
                Message(f"用户 {user_id} 已从Ena黑名单移除！\n操作人：{event.user_id}")
            )
        else:
            await manager.finish("黑名单移除失败，请检查格式或文件权限")


@query_blacklist.handle()
async def handle_query(event: GroupMessageEvent, msg: str = EventPlainText()):
    if event.group_id != auth_group:
        return

    match = re.match(r"^查询黑名单\s*(\d+)?$", msg.strip())
    if not match:
        return

    target_id = match.group(1)

    if not target_id:
        await query_blacklist.finish()
        return

    user_id = int(target_id)
    blacklist = await get_blacklist()

    if user_id in blacklist:
        result = f"用户 {user_id} 存在于黑名单中"
    else:
        result = f"用户 {user_id} 不在黑名单中"

    await query_blacklist.finish(Message(result))