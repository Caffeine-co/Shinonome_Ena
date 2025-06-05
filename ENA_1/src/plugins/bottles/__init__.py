import aiofiles
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import nonebot
from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageSegment,
    MessageEvent,
)
from nonebot.params import EventPlainText, RegexGroup

# ========== 权限配置 ==========
WHITELIST_PATH = Path("Your_bot_project_absolute_path/src/plugins/group_whitelist.json")
BLACKLIST_PATH = Path("Your_bot_project_absolute_path/src/plugins/user_blacklist.json")
ADMIN_GROUP_ID = Your_own_dev_group_number
ADMIN_QQ = Your_own_qq_number
BOTTLE_FILE = Path(__file__).parent / "bottles.json"
MAX_DAILY_LIMIT = 1
EXEMPT_USER_ID = "Your_own_qq_number"
DATA_FILE = Path(__file__).parent / "usage_data_bottles.json"

async def check_group_whitelist(group_id: int) -> bool:
    try:
        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            whitelist = json.loads(content)

            registered_groups = {entry["group_id"] for entry in whitelist}
            return group_id in registered_groups

    except (FileNotFoundError, json.JSONDecodeError):
        return False
    except KeyError:
        return False
    except Exception as e:
        print(f"白名单核查异常: {str(e)}")
        return False


async def check_user_blacklist(user_id: int) -> bool:
    try:
        async with aiofiles.open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            blacklist = json.loads(content)
            return user_id in blacklist
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return True
    except Exception:
        return True


async def check_usage(user_id: str):
    if user_id == EXEMPT_USER_ID:
        return True

    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        async with aiofiles.open(DATA_FILE, "r") as f:
            try:
                data = json.loads(await f.read())
            except json.JSONDecodeError:
                data = {}
    except FileNotFoundError:
        async with aiofiles.open(DATA_FILE, "w") as f:
            await f.write(json.dumps({}))
        data = {}

    record = data.get(user_id, {})
    if record.get("date") != current_date:
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    if new_count > MAX_DAILY_LIMIT:
        return False

    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


throw_bottle = on_fullmatch("扔漂流瓶")
pick_bottle = on_fullmatch("捡漂流瓶")
delete_bottle = on_regex(r"^删除漂流瓶(\d+)$")
view_bottle = on_regex(r"^查看漂流瓶(\d*)$")

async def read_bottles() -> List[Optional[Dict]]:
    if not os.path.exists(BOTTLE_FILE):
        return []
    try:
        async with aiofiles.open(BOTTLE_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content) if content else []
    except:
        return []


async def write_bottles(bottles: List[Optional[Dict]]):
    async with aiofiles.open(BOTTLE_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(bottles, ensure_ascii=False, indent=2))


async def save_bottle(data: Dict) -> Tuple[int, bool]:
    bottles = await read_bottles()
    for index, item in enumerate(bottles):
        if item is None:
            data["bottle_id"] = index + 1
            bottles[index] = data
            await write_bottles(bottles)
            return index + 1, False
    data["bottle_id"] = len(bottles) + 1
    bottles.append(data)
    await write_bottles(bottles)
    return len(bottles), True

@throw_bottle.handle()
async def throw_start(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.get_user_id()
    if not (await check_usage(user_id)):
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "今天已经扔过瓶子了，明天再来吧"
        )

    await throw_bottle.send(
        MessageSegment.reply(event.message_id) + "• 输入文本写进漂流瓶\n• 输入“退出”取消扔漂流瓶\n• 请勿在漂流瓶中输入违规或不宜内容，一经发现立刻拉黑"
    )


@throw_bottle.got("content")
async def throw_get_content(
        bot: Bot,
        event: GroupMessageEvent,
        content: str = EventPlainText()
):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if content.strip() == "退出":
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "已取消扔漂流瓶"
        )

    try:
        group_info = await bot.get_group_info(group_id=event.group_id)
        group_name = group_info["group_name"]
    except Exception as e:
        group_name = f"未知群聊（{str(e)}）"

    bottle_data = {
        "user_id": event.user_id,
        "nickname": event.sender.card or event.sender.nickname,
        "group_id": event.group_id,
        "group_name": group_name,
        "content": content.strip(),
        "timestamp": int(time.time())
    }

    bottle_id, is_new = await save_bottle(bottle_data)

    admin_msg = (
        f"新的漂流瓶:No.{bottle_id}\n"
        f"来自：{bottle_data['nickname']}({event.user_id})\n"
        f"群聊：{group_name}({event.group_id})\n"
        f"内容：{content.strip()}"
    )
    await bot.send_group_msg(group_id=ADMIN_GROUP_ID, message=admin_msg)

    reply = f"漂流瓶No.{bottle_id}已扔进空无一人的湖中"
    await throw_bottle.finish(MessageSegment.reply(event.message_id) + reply)

@pick_bottle.handle()
async def pick_process(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    bottles = await read_bottles()
    valid_bottles = [b for b in bottles if b is not None]

    if not valid_bottles:
        await pick_bottle.finish(
            MessageSegment.reply(event.message_id) + "暂时没有漂流瓶哦～"
        )

    bottle = random.choice(valid_bottles)

    msg = []

    text = MessageSegment.text("Ena为你捡到了一个漂流瓶")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"编号：No.{bottle['bottle_id']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"来自：{bottle['nickname']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"内容：\n{bottle['content']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=event.group_id,
            messages=msg
        )

@delete_bottle.handle()
async def delete_process(
        bot: Bot,
        event: GroupMessageEvent,
        reg: Tuple[str, ...] = RegexGroup()
):
    try:
        bottle_id = int(reg[0])
        index = bottle_id - 1
    except ValueError:
        await delete_bottle.finish("无效的编号格式", reply_message=True)
        return

    bottles = await read_bottles()
    if index < 0 or index >= len(bottles) or bottles[index] is None:
        await delete_bottle.finish(f"你要删除的漂流瓶No.{bottle_id}不存在哦～", reply_message=True)
        return

    bottle = bottles[index]
    current_user_id = event.user_id
    bottle_owner_id = bottle["user_id"]

    if current_user_id != ADMIN_QQ and current_user_id != bottle_owner_id:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + "Ena认为你没有权限删除这个漂流瓶哦～"
        )
        return

    bottles[index] = None
    await write_bottles(bottles)

    await delete_bottle.finish(
        MessageSegment.reply(event.message_id) + f"Ena已帮你删除漂流瓶No.{bottle_id}"
    )

@view_bottle.handle()
async def view_bottle_process(bot: Bot, event: MessageEvent, reg: Tuple[str, ...] = RegexGroup()):
    if not await check_group_whitelist(event.group_id):
        return
    if await check_user_blacklist(event.user_id):
        return

    bottle_id_str = reg[0]
    user_id = event.user_id

    bottles = await read_bottles()
    user_bottles = []
    for idx, bottle in enumerate(bottles):
        if bottle and str(bottle["user_id"]) == str(user_id):
            user_bottles.append((idx + 1, bottle))

    if not user_bottles:
        await view_bottle.finish("你还没有扔过任何漂流瓶哦～", reply_message=True)

    if bottle_id_str:
        try:
            target_id = int(bottle_id_str)
            target_bottle = None
            for idx, bottle in enumerate(bottles):
                if bottle and (idx + 1) == target_id:
                    target_bottle = bottle
                    break

            if not target_bottle:
                await view_bottle.finish(f"Ena没有找到你扔过的No.{target_id}漂流瓶呢", reply_message=True)

            if str(target_bottle["user_id"]) != str(user_id):
                await view_bottle.finish(
                    MessageSegment.reply(event.message_id) +
                    f"漂流瓶No.{target_id}不属于你哦"
                )

            dt = datetime.fromtimestamp(target_bottle["timestamp"])
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            msg = []

            text = MessageSegment.text(f"昵称：{target_bottle['nickname']}\nQQ：{target_bottle['user_id']}\n昵称为扔漂流瓶时记录的群内昵称")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶编号：No.{target_id}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶扔出时间：{time_str}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶内容：\n{bottle['content']}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            if isinstance(event, GroupMessageEvent):
                await bot.send_group_forward_msg(
                    group_id=event.group_id,
                    messages=msg
                )
                
        except ValueError:
            await view_bottle.finish("请输入有效的漂流瓶编号", reply_message=True)


    else:
        sorted_bottles = sorted(user_bottles, key=lambda x: x[1]["timestamp"], reverse=True)

        user_id = event.user_id
        nickname = event.sender.card or event.sender.nickname
        
        msg = []

        user_info = f"昵称：{nickname}\nQQ：{user_id}"

        msg.append({
            "type": "node",
            "data": {
                "name": "Shinonome Ena",
                "uin": bot.self_id,
                "content": MessageSegment.text(user_info)
            }
        })

        total_count = len(sorted_bottles)
        display_count = min(100, total_count)
        header = f"Ena为你捞起了你扔过的所有漂流瓶，共{total_count}个"
        if total_count > 100:
            header += f"，显示最近{display_count}个"

        msg.append({
            "type": "node",
            "data": {
                "name": "Shinonome Ena",
                "uin": bot.self_id,
                "content": MessageSegment.text(header)
            }
        })

        content_lines = []
        for num, bottle in sorted_bottles[:100]:
            dt = datetime.fromtimestamp(bottle["timestamp"])
            time_str = dt.strftime("%m-%d %H:%M")
            line = f"🆔 No.{num} | 🕒 {time_str} | 👥 {bottle['group_name']}"
            content_lines.append(line)

        if total_count > 100:
            content_lines.append(f"\n查看完整列表请使用具体编号查询")

        chunk_size = 10
        for i in range(0, len(content_lines), chunk_size):
            chunk = content_lines[i:i + chunk_size]
            text = MessageSegment.text("\n".join(chunk))
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

        if isinstance(event, GroupMessageEvent):
            await bot.send_group_forward_msg(
                group_id=event.group_id,
                messages=msg
            )