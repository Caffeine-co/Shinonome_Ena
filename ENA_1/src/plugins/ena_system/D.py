# --------------------------
# 导入区域
# --------------------------
import aiosqlite
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import EventPlainText, RegexGroup

from  ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one, time_restriction


# --------------------------
# 配置区域
# --------------------------
ADMIN_GROUP_ID = 1017564050
ADMIN_QQ = 2083909754
DB_FILE = Path(__file__).parent / "resources/D/bottles.db"


# --------------------------
# 数据库初始化
# --------------------------
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bottles (
                bottle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nickname TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                deleted BOOLEAN DEFAULT 0
            )
        ''')

        await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bottles_deleted 
                    ON bottles (deleted)
                ''')
        await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bottles_user_id 
                    ON bottles (user_id)
                ''')
        await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bottles_timestamp 
                    ON bottles (timestamp DESC)
                ''')
        await db.commit()


# --------------------------
# 事件响应器
# --------------------------
throw_bottle = on_fullmatch("扔漂流瓶")
pick_bottle = on_fullmatch("捡漂流瓶")
delete_bottle = on_regex(r"^删除漂流瓶(\d+)$")
view_bottle = on_regex(r"^查看漂流瓶(\d*)$")


# --------------------------
# 数据库操作
# --------------------------
async def insert_bottle(data: Dict) -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            INSERT INTO bottles (user_id, nickname, group_id, group_name, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'],
            data['nickname'],
            data['group_id'],
            data['group_name'],
            data['content'],
            data['timestamp']
        ))
        await db.commit()
        return cursor.lastrowid


async def get_random_bottle() -> Optional[Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('SELECT MAX(bottle_id) AS max_id FROM bottles WHERE deleted = 0')
        max_row = await cursor.fetchone()
        max_id = max_row['max_id'] if max_row and max_row['max_id'] else 0

        if max_id == 0:
            return None

        bottle = None
        attempts = 0
        max_attempts = 10

        while bottle is None and attempts < max_attempts:
            random_id = random.randint(1, max_id)

            cursor = await db.execute('''
                SELECT * FROM bottles 
                WHERE bottle_id >= ? AND deleted = 0 
                ORDER BY bottle_id 
                LIMIT 1
            ''', (random_id,))

            bottle = await cursor.fetchone()
            attempts += 1

        return dict(bottle) if bottle else None


async def get_bottle_by_id(bottle_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM bottles WHERE bottle_id = ?', (bottle_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def mark_bottle_deleted(bottle_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE bottles SET deleted = 1 WHERE bottle_id = ?', (bottle_id,))
        await db.commit()


async def get_user_bottles(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT * FROM bottles 
            WHERE user_id = ? AND deleted = 0 
            ORDER BY timestamp DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def count_valid_bottles() -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            SELECT COUNT(*) FROM bottles 
            WHERE deleted = 0 AND id IN (
                SELECT bottle_id FROM bottles WHERE deleted = 0
            )
        ''')
        count = await cursor.fetchone()
        return count[0] if count else 0


# --------------------------
# 事件处理
# --------------------------
@throw_bottle.handle()
async def throw_bottle_handler(event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    user_id = event.user_id
    if not (await check_usage_one(user_id, "usage_data_D_1", 1)):
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "今天已经扔过瓶子了，明天再来吧"
        )

    await init_db()

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

    if await time_restriction():
        return
    
    if not content:
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "您未输入任何文本哦"
        )

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

    bottle_id = await insert_bottle(bottle_data)

    admin_msg = (
        f"新的漂流瓶:No.{bottle_id}\n"
        f"来自：{bottle_data['nickname']}({event.user_id})\n"
        f"群聊：{group_name}({event.group_id})\n"
        f"内容：{content.strip()}"
    )
    await bot.send_group_msg(group_id=ADMIN_GROUP_ID, message=admin_msg)

    reply = f"漂流瓶No.{bottle_id}已扔进25時のセカイ的湖中"
    await throw_bottle.finish(
        MessageSegment.reply(event.message_id) + reply
    )


@pick_bottle.handle()
async def pick_bottle_handler(
        bot: Bot,
        event: GroupMessageEvent
):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    user_id = event.user_id
    if not (await check_usage_one(user_id, "usage_data_D_2", 2)):
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "今天已经捡了很多瓶子了，明天再来吧"
        )

    await init_db()

    bottle = await get_random_bottle()

    if not bottle:
        await pick_bottle.finish(
            MessageSegment.reply(event.message_id) + "暂时没有漂流瓶哦～"
        )

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
async def delete_bottle_handler(
        event: GroupMessageEvent,
        reg: Tuple[str, ...] = RegexGroup()
):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    if await time_restriction():
        return

    await init_db()

    try:
        bottle_id = int(reg[0])

    except ValueError:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + "无效的编号格式"
        )


    bottle = await get_bottle_by_id(bottle_id)
    if not bottle:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + f"你要删除的漂流瓶No.{bottle_id}不存在哦～"
        )

    if bottle['deleted']:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + f"漂流瓶No.{bottle_id}已经被删除啦～"
        )

    current_user_id = event.user_id
    bottle_owner_id = bottle["user_id"]

    if current_user_id != ADMIN_QQ and current_user_id != bottle_owner_id:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + "Ena认为你没有权限删除这个漂流瓶哦～"
        )

    await mark_bottle_deleted(bottle_id)

    await delete_bottle.finish(
        MessageSegment.reply(event.message_id) + f"Ena已经帮你删除漂流瓶No.{bottle_id}啦～"
    )


@view_bottle.handle()
async def view_bottle_handler(
        bot: Bot,
        event: GroupMessageEvent,
        reg: Tuple[str, ...] = RegexGroup()
):
    if not await check_group_whitelist(event.group_id):
        return
    if await check_user_blacklist(event.user_id):
        return
    if await time_restriction():
        return

    await init_db()

    bottle_id_str = reg[0]
    user_id = event.user_id

    if bottle_id_str:
        try:
            bottle_id = int(bottle_id_str)
            bottle = await get_bottle_by_id(bottle_id)

            if not bottle:
                await view_bottle.finish(
                    MessageSegment.reply(event.message_id) + f"Ena没有找到No.{bottle_id}漂流瓶呢～"
                )

            if bottle['deleted']:
                await view_bottle.finish(
                    MessageSegment.reply(event.message_id) + f"漂流瓶No.{bottle_id}已经被删除啦～"
                )

            if bottle["user_id"] != user_id:
                await view_bottle.finish(
                    MessageSegment.reply(event.message_id) + f"漂流瓶No.{bottle_id}不属于你哦～"
                )

            dt = datetime.fromtimestamp(bottle["timestamp"])
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            msg = []

            text = MessageSegment.text(f"昵称：{bottle['nickname']}\nQQ：{bottle['user_id']}\n昵称为扔漂流瓶时记录的群内昵称")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶编号：No.{bottle_id}")
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
            await view_bottle.finish(
                MessageSegment.reply(event.message_id) + "请输入有效的漂流瓶编号"
            )

    else:
        user_bottles = await get_user_bottles(user_id)
        if not user_bottles:
            await view_bottle.finish(
                MessageSegment.reply(event.message_id) + "你还没有扔过任何漂流瓶哦～"
            )

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

        total_count = len(user_bottles)
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
        for bottle in user_bottles[:100]:
            dt = datetime.fromtimestamp(bottle["timestamp"])
            time_str = dt.strftime("%m-%d %H:%M")
            line = f"🆔 No.{bottle['bottle_id']} | 🕒 {time_str} | 👥 {bottle['group_name']}"
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