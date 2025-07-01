import json
import re
from pathlib import Path
import aiofiles
from nonebot import get_driver, on_message, on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, ActionFailed
from nonebot.exception import MatcherException
from nonebot.params import EventPlainText
from typing import Union

global_config = get_driver().config
admin_id = int(global_config.admin_id)
auth_group = int(global_config.auth_group)

WHITELIST_PATH = Path("***/ENA_1/src/plugins/ena_system/resources/use_limit/group_whitelist.json")

if not WHITELIST_PATH.exists():
    WHITELIST_PATH.write_text("[]", encoding='utf-8')

manager = on_message(block=True)
query_auth = on_message(block=True, rule=lambda event: event.group_id == auth_group)  # 仅在授权群生效
query_current = on_fullmatch("查询授权")
change_owner = on_message(block=True, rule=lambda event: event.user_id == admin_id)  # 直接整合管理员验证


async def update_whitelist(group_id: int, operation: str, user_id: int) -> Union[str, bool]:
    try:
        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
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

        async with aiofiles.open(WHITELIST_PATH, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(whitelist, indent=4))
        return status

    except Exception as e:
        print(f"白名单更新失败: {str(e)}")
        return False


async def load_whitelist() -> list:
    try:
        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
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
    if apply_match := re.match(r"^申请授权\s*(\d+)$", msg.strip()):
        if event.group_id != auth_group:
            return

        group_id = int(apply_match.group(1))
        user_id = event.user_id

        try:
            group_list = await bot.get_group_list()
            if group_id not in {g["group_id"] for g in group_list}:
                await manager.finish(f"🎨授权失败啦，可能是未入群 {group_id} 呢")
        except:
            return

        try:
            member_info = await bot.get_group_member_info(
                group_id=group_id,
                user_id=user_id,
                no_cache=True
            )
            role = member_info.get("role", "")
            if role not in ["owner", "admin"]:
                await manager.finish("🎨授权失败啦，只有群主或管理员才能申请授权呢")

        except ActionFailed as e:
            print(f"权限验证失败: {e}")
            await manager.finish("🎨权限验证失败：请确保能获取成员信息")
        except MatcherException:
            raise
        except Exception as e:
            print(f"权限验证异常: {e}")
            await manager.finish("🎨权限验证时发生未知错误")

        result = await update_whitelist(group_id, "add", user_id)

        if result == "added":
            await manager.finish(
                Message(f"🎨群聊 {group_id} 授权成功咯！\n🎨领养人：{user_id}\n🎨领养人请不要退出本群和所授权的群哟~"))
        elif result == "duplicate":
            whitelist = await load_whitelist()
            entry = next(x for x in whitelist if x["group_id"] == group_id)
            await manager.finish(Message(f"🎨该群已授权！\n🎨领养人：{entry['user_id']}\n🎨若需更换领养人请联系咖啡不甜"))
        else:
            await manager.finish("🎨授权失败啦，请检查群号格式或联系bot主")

    elif cancel_match := re.match(r"^取消授权\s*(\d+)$", msg.strip()):
        if event.user_id != admin_id:
            return

        group_id = int(cancel_match.group(1))
        result = await update_whitelist(group_id, "remove", 0)

        if result == "removed":
            await manager.finish(Message(f"🎨已取消群 {group_id} 授权"))
        elif result == "not_found":
            await manager.finish(f"🎨群 {group_id} 未授权")
        else:
            await manager.finish("取消授权失败，请检查群号或文件权限")


@query_auth.handle()
async def handle_query_auth(event: GroupMessageEvent, msg: str = EventPlainText()):
    if match := re.match(r"^查询授权\s*(\d+)$", msg.strip()):
        target_group = int(match.group(1))
        whitelist = await load_whitelist()
        entry = next((x for x in whitelist if x["group_id"] == target_group), None)

        if entry:
            await query_auth.finish(
                f"🎨群聊 {target_group} 已授权领养Ena\n"
                f"🎨领养人：{entry['user_id']}"
            )
        else:
            await query_auth.finish(f"🎨群聊 {target_group} 未授权领养Ena")


@query_current.handle()
async def handle_query_current(event: GroupMessageEvent):
    current_group = event.group_id
    whitelist = await load_whitelist()
    entry = next((x for x in whitelist if x["group_id"] == current_group), None)

    if entry:
        await query_current.finish(
            f"🎨本群已授权领养Ena\n"
            f"🎨领养人：{entry['user_id']}"
        )
    else:
        await query_current.finish(f"🎨本群未授权领养Ena")


@change_owner.handle()
async def handle_change_owner(
        event: GroupMessageEvent,
        msg: str = EventPlainText()
):
    if str(event.user_id) != str(admin_id):
        return

    pattern = r"^更换群聊\s*(\d+)\s*的领养人为\s*(\d+)$"
    if match := re.match(pattern, msg.strip()):
        group_id = int(match.group(1))
        new_user = int(match.group(2))

        whitelist = await load_whitelist()

        target = next((x for x in whitelist if x["group_id"] == group_id), None)

        if not target:
            await change_owner.finish(f"🎨群聊 {group_id} 还没有授权，无法更换领养人哦")

        try:
            target["user_id"] = new_user
            async with aiofiles.open(WHITELIST_PATH, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(whitelist, indent=4))
        except Exception as e:
            print(f"领养人更换失败: {str(e)}")

        await change_owner.finish(
            Message(
                f"🎨领养人更换成功啦！\n🎨群号：{group_id}\n🎨新领养人：{new_user}\n🎨请新领养人请不要退出本群和所授权的群哟~")
        )