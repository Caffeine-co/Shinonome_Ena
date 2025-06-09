import json
import re
from pathlib import Path
from typing import Optional
import aiofiles
from nonebot import get_driver, on_message, on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import EventPlainText
from nonebot.permission import SUPERUSER

global_config = get_driver().config
admin_id = int(global_config.admin_id)

AICHAT_WHITELIST_PATH = Path("***/ENA_1/src/plugins/aichat/aichat_group_whitelist.json")

if not AICHAT_WHITELIST_PATH.exists():
    AICHAT_WHITELIST_PATH.write_text("[]", encoding='utf-8')

manager = on_message(block=True)


async def update_whitelist(group_id: int, operation: str, user_id: int) -> bool:
    try:
        async with aiofiles.open(AICHAT_WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            whitelist = json.loads(content) if content else []

        status = ""

        if operation == "add":
            exist_entry = next((x for x in whitelist if x["group_id"] == group_id), None)

            if exist_entry:
                status = "duplicate"
            else:
                whitelist.append({"group_id": group_id, "user_id": user_id})
                status = "added"
        elif operation == "remove":
            initial_count = len(whitelist)
            whitelist = [x for x in whitelist if x["group_id"] != group_id]

            if len(whitelist) < initial_count:
                status = "removed"
            else:
                status = "not_found"

        async with aiofiles.open(AICHAT_WHITELIST_PATH, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(whitelist, indent=4))
        return status

    except Exception as e:
        print(f"白名单更新失败: {str(e)}")
        return False


async def load_whitelist() -> list:
    try:
        async with aiofiles.open(AICHAT_WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content else []
    except Exception as e:
        print(f"读取白名单失败: {str(e)}")
        return []


@manager.handle()
async def unified_manager_handler(
        bot: Bot,
        event: GroupMessageEvent,
        msg: str = EventPlainText()
):
    if apply_match := re.match(r"^开启ai聊天\s*(\d+)$", msg.strip()):
        
        if event.user_id != admin_id:
            return

        group_id = int(apply_match.group(1))
        user_id = event.user_id

        try:
            group_list = await bot.get_group_list()
            if group_id not in {g["group_id"] for g in group_list}:
                await manager.finish(f"🎨开启失败啦，可能是未入群 {group_id} 捏")
        except:
            return

        result = await update_whitelist(group_id, "add", user_id)

        if result == "added":
            await manager.finish(Message(f"🎨已开启群聊 {group_id} 的ai聊天功能"))
        elif result == "duplicate":
            whitelist = await load_whitelist()
            entry = next(x for x in whitelist if x["group_id"] == group_id)
            await manager.finish(Message(f"🎨该群已开启ai聊天功能"))
        else:
            await manager.finish("🎨开启失败啦，请检查群号格式或联系bot主")

    elif cancel_match := re.match(r"^关闭ai聊天\s*(\d+)$", msg.strip()):
        if event.user_id != admin_id:
            return

        group_id = int(cancel_match.group(1))
        result = await update_whitelist(group_id, "remove", 0)

        if result == "removed":
            await manager.finish(Message(f"🎨已关闭群 {group_id} 的ai聊天功能"))
        elif result == "not_found":
            await manager.finish(f"🎨群 {group_id} 未开启ai聊天功能")
        else:
            await manager.finish("关闭失败啦，请检查群号或文件权限")