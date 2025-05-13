import aiofiles
import json
import os
import random
import time
import nonebot
from pathlib import Path
from PIL import Image
from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.plugin import on_message
from nonebot.rule import Rule
from nonebot.typing import T_State

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

CHARACTER_IMAGE_DIR = Path("Your_path/ENA_1/src/plugins/characters")
TEMP_DIR = Path("Your_path/ENA_1/src/plugins/temp")
WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"
TIMEOUT = 30
ANSWER_RETENTION = TIMEOUT + 10
TRIGGER_KEYWORD = "猜卡面"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

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
    except Exception as e:
        return True

sessions = {}
message_id_to_answer = {}

def get_character_info(character_dir: Path) -> tuple[str, list[str]]:
    json_path = character_dir / f"{character_dir.name}.json"
    default_display_name = character_dir.name
    default_aliases = [default_display_name.lower()]

    if not json_path.exists():
        return default_display_name, default_aliases

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            display_name = data.get("display_name", default_display_name)
            aliases = [a.lower() for a in data.get("aliases", [display_name.lower()])]
            if not aliases:
                aliases = [display_name.lower()]
            return display_name, aliases
    except Exception:
        return default_display_name, default_aliases


def select_random_character_image() -> tuple[Path | None, Path | None, str | None, list[str] | None]:
    if not CHARACTER_IMAGE_DIR.exists():
        return None, None, None, None

    character_dirs = [d for d in CHARACTER_IMAGE_DIR.iterdir() if d.is_dir()]
    if not character_dirs:
        return None, None, None, None

    character_dir = random.choice(character_dirs)
    images = [f for f in character_dir.glob("*") if f.is_file() and not f.name.endswith(".json")]
    if not images:
        return None, None, None, None

    image_path = random.choice(images)
    display_name, aliases = get_character_info(character_dir)
    return character_dir, image_path, display_name, aliases


def crop_image(image_path: Path) -> Path:
    img = Image.open(image_path)
    w, h = img.size

    crop_width = 200
    crop_height = 200

    if crop_width > w or crop_height > h:
        crop_width = min(crop_width, w)
        crop_height = min(crop_height, h)

    left = random.randint(0, w - crop_width)
    upper = random.randint(0, h - crop_height)
    right = left + crop_width
    lower = upper + crop_height

    cropped = img.crop((left, upper, right, lower))
    temp_file = TEMP_DIR / f"{time.time_ns()}.png"
    cropped.save(temp_file)
    return temp_file
async def check_reply(event: GroupMessageEvent) -> bool:
    if not event.reply:
        return False

    session_key = (event.user_id, event.group_id)
    if session_key in sessions:
        return event.reply.message_id == sessions[session_key]["bot_msg_id"]

    return event.reply.message_id in message_id_to_answer


async def is_trigger_keyword(event: MessageEvent) -> bool:
    return event.get_plaintext() == TRIGGER_KEYWORD
trigger_matcher = on_message(
    rule=Rule(is_trigger_keyword) & Rule(lambda event: isinstance(event, GroupMessageEvent)),
    block=True
)

reply_matcher = on_message(
    rule=Rule(check_reply) & Rule(lambda event: isinstance(event, GroupMessageEvent)),
    block=True
)

@scheduler.scheduled_job("interval", minutes=10)
def cleanup_temp_files():
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            file.unlink()


@scheduler.scheduled_job("interval", seconds=10, misfire_grace_time=30, coalesce=True)
async def cleanup_sessions():
    current_time = time.time()
    expired_keys = [k for k, v in sessions.items() if current_time - v["timestamp"] > TIMEOUT]

    for key in expired_keys:
        session = sessions.pop(key, None)
        if session:
            try:
                bot = nonebot.get_bot()
                reply_msg = MessageSegment.reply(session["trigger_msg_id"]) + \
                            MessageSegment.text("时间到！正确答案是：") + \
                            MessageSegment.text(session["display_name"]) + \
                            MessageSegment.image(session["original_image"])
                await bot.send_group_msg(group_id=key[1], message=reply_msg)
                message_id_to_answer[session["bot_msg_id"]] = {
                    "display_name": session["display_name"],
                    "original_image": session["original_image"],
                    "timestamp": current_time
                }
            except Exception as e:
                nonebot.logger.error(f"发送超时提示失败：{e}")
            finally:
                if session["cropped_image"].exists():
                    session["cropped_image"].unlink()

    expired_messages = [msg_id for msg_id, data in message_id_to_answer.items()
                        if current_time - data["timestamp"] > ANSWER_RETENTION]
    for msg_id in expired_messages:
        del message_id_to_answer[msg_id]

@trigger_matcher.handle()
async def handle_trigger(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    session_key = (event.user_id, event.group_id)

    if session_key in sessions:
        if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
            del sessions[session_key]
        else:
            await trigger_matcher.finish("您有一个进行中的游戏，请先完成或等待超时。")

    character_dir, image_path, display_name, aliases = select_random_character_image()
    if not all([character_dir, image_path, display_name, aliases]):
        await trigger_matcher.finish("暂时无法开始游戏，请联系bot主检查资源")

    try:
        cropped_path = crop_image(image_path)
    except Exception as e:
        nonebot.logger.error(f"图片处理失败：{e}")
        await trigger_matcher.finish("图片处理失败，请稍后再试")

    try:
        message = MessageSegment.reply(event.message_id) + \
                  MessageSegment.text("你有30秒的时间回答") + \
                  MessageSegment.image(cropped_path)
        result = await bot.send(event, message)

        sessions[session_key] = {
            "display_name": display_name,
            "aliases": aliases,
            "original_image": image_path,
            "cropped_image": cropped_path,
            "timestamp": time.time(),
            "bot_msg_id": result["message_id"],
            "trigger_msg_id": event.message_id
        }
    except Exception as e:
        await trigger_matcher.finish("游戏初始化失败，请稍后再试")


@reply_matcher.handle()
async def handle_reply(bot: Bot, event: GroupMessageEvent):
    reply_msg_id = event.reply.message_id
    session_key = (event.user_id, event.group_id)

    if session_key in sessions:
        session = sessions[session_key]
        current_time = time.time()

        if current_time - session["timestamp"] > TIMEOUT:
            del sessions[session_key]
            reply_msg = MessageSegment.reply(event.message_id) + \
                        MessageSegment.text("回答超时！正确答案是：") + \
                        MessageSegment.text(session["display_name"]) + \
                        MessageSegment.image(session["original_image"])
            await reply_matcher.finish(reply_msg)

        user_input = event.get_plaintext().strip().lower()
        if user_input == "结束猜卡面":
            del sessions[session_key]
            await reply_matcher.finish("已退出当前游戏", reply_message=True)

        is_correct = user_input in session["aliases"]
        reply_msg = MessageSegment.reply(event.message_id)

        if is_correct:
            reply_msg += MessageSegment.text("锵锵！猜对啦")
        else:
            reply_msg += MessageSegment.text(f"猜错了哦，正确答案是：{session['display_name']}")

        reply_msg += MessageSegment.image(session["original_image"])
        await reply_matcher.send(reply_msg)

        del sessions[session_key]
        if session["cropped_image"].exists():
            session["cropped_image"].unlink()
        return

    if reply_msg_id in message_id_to_answer:
        data = message_id_to_answer[reply_msg_id]
        reply_msg = MessageSegment.reply(event.message_id) + \
                    MessageSegment.text("游戏已超时，正确答案是：") + \
                    MessageSegment.text(data["display_name"]) + \
                    MessageSegment.image(data["original_image"])
        await reply_matcher.finish(reply_msg)

    await reply_matcher.finish()
