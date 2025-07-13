# --------------------------
# 导入区域
# --------------------------
import json
import random
import time
import nonebot
from pathlib import Path
from PIL import Image
from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.plugin import on_message, on_fullmatch
from nonebot.rule import Rule

from ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one


# --------------------------
# 配置区域
# --------------------------
CHARACTER_IMAGE_DIR = Path(__file__).parent / "resources/K/characters"
MUSIC_IMAGE_DIR = Path(__file__).parent / "resources/K/musics"
TEMP_DIR = Path(__file__).parent / "resources/K/temp"
TIMEOUT = 30
ANSWER_RETENTION = TIMEOUT + 10

TEMP_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据存储结构
# --------------------------
sessions = {}

message_id_to_answer = {}


# --------------------------
# 核心功能函数
# --------------------------
def get_character_info(character_dir: Path) -> tuple[str, list[str]]:
    json_path = character_dir / f"{character_dir.name}.json"

    folder_name = character_dir.name

    display_name = folder_name
    aliases_list = [folder_name.lower()]

    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

                if "display_name" in data and data["display_name"]:
                    display_name = data["display_name"]

                aliases_list = []
                if "aliases" in data and isinstance(data["aliases"], list):
                    aliases_list = [a.lower() for a in data["aliases"] if a]

                if display_name.lower() not in aliases_list:
                    aliases_list.append(display_name.lower())

                if folder_name.lower() not in aliases_list:
                    aliases_list.append(folder_name.lower())

                if not aliases_list:
                    aliases_list = [display_name.lower()]

        except Exception as e:
            nonebot.logger.error(f"解析角色JSON失败: {e}，使用默认值")

    return display_name, aliases_list

def get_music_info(music_dir: Path) -> tuple[str, list[str]]:
    json_path = music_dir / f"{music_dir.name}.json"

    folder_name = music_dir.name

    display_name = folder_name
    aliases_list = [folder_name.lower()]

    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

                if "display_name" in data and data["display_name"]:
                    display_name = data["display_name"]

                aliases_list = []
                if "aliases" in data and isinstance(data["aliases"], list):
                    aliases_list = [a.lower() for a in data["aliases"] if a]

                if display_name.lower() not in aliases_list:
                    aliases_list.append(display_name.lower())

                if folder_name.lower() not in aliases_list:
                    aliases_list.append(folder_name.lower())

                if not aliases_list:
                    aliases_list = [display_name.lower()]

        except Exception as e:
            nonebot.logger.error(f"解析歌曲JSON失败: {e}，使用默认值")

    return display_name, aliases_list

def select_random_character_image() -> tuple[Path | None, Path | None, str | None, list[str] | None]:
    if not CHARACTER_IMAGE_DIR.exists():
        return None, None, None, None

    character_dirs = [d for d in CHARACTER_IMAGE_DIR.iterdir() if d.is_dir()]
    if not character_dirs:
        return None, None, None, None

    character_dir = random.choice(character_dirs)

    images = [f for f in character_dir.glob("*")
              if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
              and not f.name.endswith(".json")]

    if not images:
        return None, None, None, None

    image_path = random.choice(images)
    display_name, aliases = get_character_info(character_dir)
    return character_dir, image_path, display_name, aliases

def select_random_music_image() -> tuple[Path | None, Path | None, str | None, list[str] | None]:
    if not MUSIC_IMAGE_DIR.exists():
        return None, None, None, None

    music_dirs = [d for d in MUSIC_IMAGE_DIR.iterdir() if d.is_dir()]
    if not music_dirs:
        return None, None, None, None

    music_dir = random.choice(music_dirs)

    images = [f for f in music_dir.glob("*")
              if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
              and not f.name.endswith(".json")]

    if not images:
        return None, None, None, None

    image_path = random.choice(images)
    display_name, aliases = get_music_info(music_dir)
    return music_dir, image_path, display_name, aliases

def crop_character_image(image_path: Path) -> Path:
    img = Image.open(image_path)
    w, h = img.size

    crop_width, crop_height = 200, 200

    if crop_width > w or crop_height > h:
        crop_width = min(crop_width, w)
        crop_height = min(crop_height, h)

    left = random.randint(0, w - crop_width)
    upper = random.randint(0, h - crop_height)
    right = left + crop_width
    lower = upper + crop_height

    cropped = img.crop((left, upper, right, lower))

    temp_file = TEMP_DIR / f"character_{time.time_ns()}.png"
    cropped.save(temp_file)
    return temp_file

def crop_music_image(image_path: Path) -> Path:
    img = Image.open(image_path)
    w, h = img.size

    crop_width, crop_height = 100, 100

    if crop_width > w or crop_height > h:
        crop_width = min(crop_width, w)
        crop_height = min(crop_height, h)

    left = random.randint(0, w - crop_width)
    upper = random.randint(0, h - crop_height)

    cropped = img.crop((left, upper, left + crop_width, upper + crop_height))

    temp_file = TEMP_DIR / f"music_{time.time_ns()}.png"
    cropped.save(temp_file)
    return temp_file


# --------------------------
# 定时任务
# --------------------------
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

@scheduler.scheduled_job("interval", minutes=10)
def cleanup_temp_files():
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            try:
                file.unlink()
            except:
                pass

@scheduler.scheduled_job("interval", seconds=10)
async def cleanup_sessions():
    current_time = time.time()

    expired_keys = []

    for key, session in sessions.items():
        if current_time - session["timestamp"] > TIMEOUT:
            expired_keys.append(key)

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
                    try:
                        session["cropped_image"].unlink()
                    except:
                        pass

    for key in expired_keys:
        sessions.pop(key, None)

    expired_msg_ids = [
        msg_id for msg_id, data in message_id_to_answer.items()
        if current_time - data["timestamp"] > ANSWER_RETENTION
    ]
    for msg_id in expired_msg_ids:
        message_id_to_answer.pop(msg_id, None)


# --------------------------
# 消息规则检查器
# --------------------------
async def check_reply(event: GroupMessageEvent) -> bool:
    if not event.reply:
        return False

    session_key = (event.user_id, event.group_id)
    if session_key in sessions:
        return event.reply.message_id == sessions[session_key]["bot_msg_id"]

    return event.reply.message_id in message_id_to_answer


# --------------------------
# 事件响应器
# --------------------------
guess_character = on_fullmatch("猜卡面")
guess_music = on_fullmatch("猜曲绘")
reply_matcher = on_message(rule=Rule(check_reply), block=True)


# --------------------------
# 事件处理
# --------------------------
@guess_character.handle()
async def guess_character_handler(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_K", 3)):
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天游戏次数到达上限了，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    if session_key in sessions:
        if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
            del sessions[session_key]
        else:
            await guess_character.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
            )

    character_dir, image_path, display_name, aliases = select_random_character_image()
    if not all([character_dir, image_path, display_name, aliases]):
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
        )

    try:
        cropped_path = crop_character_image(image_path)

    except Exception as e:
        nonebot.logger.error(f"角色图片处理失败：{e}")
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("角色图片处理失败，请稍后再试")
        )

    try:
        message = MessageSegment.reply(event.message_id) + \
                  MessageSegment.text("你有30秒的时间回答") + \
                  MessageSegment.image(cropped_path)
        result = await bot.send(event, message)

        sessions[session_key] = {
            "game_type": "卡面",
            "display_name": display_name,
            "aliases": aliases,
            "original_image": image_path,
            "cropped_image": cropped_path,
            "timestamp": time.time(),
            "bot_msg_id": result["message_id"],
            "trigger_msg_id": event.message_id
        }

    except Exception as e:
        nonebot.logger.error(f"猜卡面游戏初始化失败：{e}")
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("猜卡面游戏初始化失败，请稍后再试")
        )


@guess_music.handle()
async def guess_music_handler(bot: Bot, event: GroupMessageEvent):
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_K", 3)):
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天的游戏次数已达上限，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    if session_key in sessions:
        if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
            del sessions[session_key]
        else:
            await guess_music.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
            )

    song_dir, image_path, display_name, aliases = select_random_music_image()
    if not all([song_dir, image_path, display_name, aliases]):
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
        )

    try:
        cropped_path = crop_music_image(image_path)

    except Exception as e:
        nonebot.logger.error(f"曲绘图片处理失败：{e}")
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("曲绘图片处理失败，请稍后再试")
        )

    try:
        message = MessageSegment.reply(event.message_id) + \
                  MessageSegment.text("你有30秒的时间回答") + \
                  MessageSegment.image(cropped_path)
        result = await bot.send(event, message)

        sessions[session_key] = {
            "game_type": "曲绘",
            "display_name": display_name,
            "aliases": aliases,
            "original_image": image_path,
            "cropped_image": cropped_path,
            "timestamp": time.time(),
            "bot_msg_id": result["message_id"],
            "trigger_msg_id": event.message_id
        }

    except Exception as e:
        nonebot.logger.error(f"游戏初始化失败：{e}")
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("游戏初始化失败，请稍后再试")
        )


@reply_matcher.handle()
async def handle_reply(event: GroupMessageEvent):
    reply_msg_id = event.reply.message_id
    session_key = (event.user_id, event.group_id)

    user_input = event.get_plaintext().strip().lower()

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

        if user_input == f"结束猜{session['game_type']}":
            del sessions[session_key]
            await reply_matcher.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("已退出当前游戏")
            )

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
            try:
                session["cropped_image"].unlink()
            except:
                pass
        return

    if reply_msg_id in message_id_to_answer:
        data = message_id_to_answer[reply_msg_id]
        reply_msg = MessageSegment.reply(event.message_id) + \
                    MessageSegment.text("游戏已超时，正确答案是：") + \
                    MessageSegment.text(data["display_name"]) + \
                    MessageSegment.image(data["original_image"])
        await reply_matcher.finish(reply_msg)

    await reply_matcher.finish()