# --------------------------
# 导入区域
# --------------------------
import json
import random
import time
import nonebot
import aiohttp
import asyncio
from pathlib import Path
from PIL import Image
from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.plugin import on_message, on_fullmatch
from nonebot.rule import Rule

from ._430_ import check_group_whitelist, check_user_blacklist, check_usage_one, time_restriction


# --------------------------
# 配置区域
# --------------------------
CHARACTER_JSON_DIR = Path(__file__).parent / "resources/K/characters"
MUSIC_JSON_DIR = Path(__file__).parent / "resources/K/musics"
TEMP_DIR = Path(__file__).parent / "resources/K/temp"

TIMEOUT = 30
ANSWER_RETENTION = TIMEOUT + 10

CHARACTER_BASE_URL = 'https://sekai-assets-bdf29c81.seiunx.net/jp-assets/startapp/character/member/'
MUSIC_BASE_URL = 'https://sekai-assets-bdf29c81.seiunx.net/jp-assets/startapp/music/jacket/'

TEMP_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据存储结构
# --------------------------
sessions = {}

message_id_to_answer = {}  # type: dict[int, dict]

session_locks = {}


# --------------------------
# 核心功能函数
# --------------------------
async def download_image(url: str, save_path: Path) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await response.read())
                    return True
    except Exception as e:
        nonebot.logger.error(f"图片下载失败: {e}")
    return False

async def select_random_character() -> tuple[Path | None, str | None, list[str] | None]:
    if not CHARACTER_JSON_DIR.exists():
        return None, None, None

    json_files = list(CHARACTER_JSON_DIR.glob("*.json"))
    if not json_files:
        return None, None, None

    json_path = random.choice(json_files)

    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        display_name = data.get("display_name", json_path.stem)

        aliases = [a.lower() for a in data.get("aliases", [])]

        if display_name.lower() not in aliases:
            aliases.append(display_name.lower())

        if not data.get("url_list"):
            return None, None, None

        relative_path = random.choice(data["url_list"])
        image_url = CHARACTER_BASE_URL + relative_path

        temp_file = TEMP_DIR / f"char_{time.time_ns()}.png"
        if await download_image(image_url, temp_file):
            return temp_file, display_name, aliases

    except Exception as e:
        nonebot.logger.error(f"角色JSON解析失败: {e}")

    return None, None, None

async def select_random_music() -> tuple[Path | None, str | None, list[str] | None]:
    if not MUSIC_JSON_DIR.exists():
        return None, None, None

    json_files = list(MUSIC_JSON_DIR.glob("*.json"))
    if not json_files:
        return None, None, None

    json_path = random.choice(json_files)

    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        display_name = data.get("display_name", json_path.stem)

        aliases = [a.lower() for a in data.get("aliases", [])]

        if display_name.lower() not in aliases:
            aliases.append(display_name.lower())

        if not data.get("url_list"):
            return None, None, None

        relative_path = random.choice(data["url_list"])
        image_url = MUSIC_BASE_URL + relative_path

        temp_file = TEMP_DIR / f"music_{time.time_ns()}.png"
        if await download_image(image_url, temp_file):
            return temp_file, display_name, aliases

    except Exception as e:
        nonebot.logger.error(f"歌曲JSON解析失败: {e}")

    return None, None, None

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

    temp_file = TEMP_DIR / f"character_crop_{time.time_ns()}.png"
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

    temp_file = TEMP_DIR / f"music_crop_{time.time_ns()}.png"
    cropped.save(temp_file)
    return temp_file


# --------------------------
# 定时任务
# --------------------------
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

@scheduler.scheduled_job("cron", hour="0", minute="0", second="0", id="clean")
def cleanup_temp_files():
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            try:
                file.unlink()
                nonebot.logger.debug(f"清理临时文件成功: {file}")
            except Exception as e:
                nonebot.logger.error(f"清理临时文件失败: {file}: {e}")
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
                for file in [session["original_image"], session["cropped_image"]]:
                    if file and file.exists():
                        try:
                            file.unlink()
                            nonebot.logger.debug(f"清理临时文件: {file}")
                        except Exception as e:
                            nonebot.logger.error(f"清理文件失败 {file}: {e}")
                            pass

    for key in expired_keys:
        sessions.pop(key, None)
        if key in session_locks:
            session_locks.pop(key, None)

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
# 会话锁处理
# --------------------------
async def get_session_lock(session_key: tuple) -> asyncio.Lock:
    if session_key not in session_locks:
        session_locks[session_key] = asyncio.Lock()
    return session_locks[session_key]


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
    if await time_restriction():
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_K", 3)):
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天游戏次数到达上限了，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    lock = await get_session_lock(session_key)

    if lock.locked():
        await guess_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("您有一个游戏正在准备中，请稍后再试")
        )

    async with lock:
        if session_key in sessions:
            if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
                del sessions[session_key]
            else:
                await guess_character.finish(
                    MessageSegment.reply(event.message_id) + \
                    MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
                )

        original_image, display_name, aliases = await select_random_character()
        if not all([original_image, display_name, aliases]):
            await guess_character.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
            )

        try:
            cropped_image = crop_character_image(original_image)

        except Exception as e:
            nonebot.logger.error(f"角色图片处理失败：{e}")
            await guess_character.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("角色图片处理失败，请稍后再试")
            )

        try:
            message = MessageSegment.reply(event.message_id) + \
                      MessageSegment.text("你有30秒的时间回答") + \
                      MessageSegment.image(cropped_image)
            result = await bot.send(event, message)

            sessions[session_key] = {
                "game_type": "卡面",
                "display_name": display_name,
                "aliases": aliases,
                "original_image": original_image,
                "cropped_image": cropped_image,
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
    if await time_restriction():
        return

    user_id = event.user_id

    if not (await check_usage_one(user_id, "usage_data_K", 3)):
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天的游戏次数已达上限，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    lock = await get_session_lock(session_key)

    if lock.locked():
        await guess_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("您有一个游戏正在准备中，请稍后再试")
        )

    async with lock:
        if session_key in sessions:
            if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
                del sessions[session_key]
            else:
                await guess_music.finish(
                    MessageSegment.reply(event.message_id) + \
                    MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
                )

        original_image, display_name, aliases = await select_random_music()
        if not all([original_image, display_name, aliases]):
            await guess_music.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
            )

        try:
            cropped_image = crop_music_image(original_image)

        except Exception as e:
            nonebot.logger.error(f"曲绘图片处理失败：{e}")
            await guess_music.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("曲绘图片处理失败，请稍后再试")
            )

        try:
            message = MessageSegment.reply(event.message_id) + \
                      MessageSegment.text("你有30秒的时间回答") + \
                      MessageSegment.image(cropped_image)
            result = await bot.send(event, message)

            sessions[session_key] = {
                "game_type": "曲绘",
                "display_name": display_name,
                "aliases": aliases,
                "original_image": original_image,
                "cropped_image": cropped_image,
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
        for file in [session["original_image"], session["cropped_image"]]:
            if file and file.exists():
                try:
                    file.unlink()
                    nonebot.logger.debug(f"清理临时文件: {file}")
                except Exception as e:
                    nonebot.logger.error(f"清理文件失败 {file}: {e}")
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