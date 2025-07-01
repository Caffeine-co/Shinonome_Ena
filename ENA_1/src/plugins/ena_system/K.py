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

from ._430_ import check_group_whitelist, check_user_blacklist, check_guessplay_usage



# --------------------------
# 配置区域
# --------------------------
CHARACTER_IMAGE_DIR = Path(__file__).parent / "resources/K/characters"  # 角色图片根目录
MUSIC_IMAGE_DIR = Path(__file__).parent / "resources/K/musics"  # 歌曲曲绘根目录
TEMP_DIR = Path(__file__).parent / "resources/K/temp"  # 临时文件目录
TIMEOUT = 30  # 游戏超时时间（秒）
ANSWER_RETENTION = TIMEOUT + 10  # 答案保留时间

# 创建必要的目录
TEMP_DIR.mkdir(parents=True, exist_ok=True)



# --------------------------
# 数据存储结构
# --------------------------
# 当前会话存储结构：{(user_id, group_id): session_data}
sessions = {}

# 存储message_id对应的答案信息（用于超时后查看）
message_id_to_answer = {}  # type: dict[int, dict]



# --------------------------
# 核心功能函数
# --------------------------
#获取显示名称与别名
def get_character_info(character_dir: Path) -> tuple[str, list[str]]:
    """
    获取角色显示名称和别名
    :param character_dir: 角色目录路径
    :return: (显示名称, 别名列表)
    逻辑：
    1. 尝试读取与目录同名的JSON文件
    2. 不存在则使用目录名作为默认显示名称
    3. 始终保证至少有一个有效别名
    """
    # JSON文件名改为角色初始名称（即目录名）
    json_path = character_dir / f"{character_dir.name}.json"
    # default_display_name = character_dir.name
    # default_aliases = [default_display_name.lower()]

    folder_name = character_dir.name

    # 默认值：使用文件夹名
    display_name = folder_name
    aliases_list = [folder_name.lower()]

    if json_path.exists():
        try:
            # 使用 utf-8-sig 编码处理 BOM 标记
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

                # 优先使用display_name
                if "display_name" in data and data["display_name"]:
                    display_name = data["display_name"]

                # 处理别名列表
                aliases_list = []
                if "aliases" in data and isinstance(data["aliases"], list):
                    aliases_list = [a.lower() for a in data["aliases"] if a]

                # 确保display_name在别名列表中（避免大小写问题）
                if display_name.lower() not in aliases_list:
                    aliases_list.append(display_name.lower())

                # 确保文件夹名在别名列表中（作为备选）
                if folder_name.lower() not in aliases_list:
                    aliases_list.append(folder_name.lower())

                # 确保至少有一个有效别名
                if not aliases_list:
                    aliases_list = [display_name.lower()]

        except Exception as e:
            nonebot.logger.error(f"解析角色JSON失败: {e}，使用默认值")

    return display_name, aliases_list


def get_music_info(music_dir: Path) -> tuple[str, list[str]]:
    """
    获取歌曲显示名称和别名
    优先级：display_name > aliases[0] > 文件夹名
    """
    json_path = music_dir / f"{music_dir.name}.json"
    # default_display_name = music_dir.name
    # default_aliases = [default_display_name.lower()]

    folder_name = music_dir.name

    # 默认值：使用文件夹名
    display_name = folder_name
    aliases_list = [folder_name.lower()]

    if json_path.exists():
        try:
            # 使用 utf-8-sig 编码处理 BOM 标记
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

                # 优先使用display_name
                if "display_name" in data and data["display_name"]:
                    display_name = data["display_name"]

                # 处理别名列表
                aliases_list = []
                if "aliases" in data and isinstance(data["aliases"], list):
                    aliases_list = [a.lower() for a in data["aliases"] if a]

                # 确保display_name在别名列表中（避免大小写问题）
                if display_name.lower() not in aliases_list:
                    aliases_list.append(display_name.lower())

                # 确保文件夹名在别名列表中（作为备选）
                if folder_name.lower() not in aliases_list:
                    aliases_list.append(folder_name.lower())

                # 确保至少有一个有效别名
                if not aliases_list:
                    aliases_list = [display_name.lower()]

        except Exception as e:
            nonebot.logger.error(f"解析歌曲JSON失败: {e}，使用默认值")

    return display_name, aliases_list


# 随机选择角色/歌曲和图片
def select_random_character_image() -> tuple[Path | None, Path | None, str | None, list[str] | None]:
    """
    随机选择角色和卡面图片
    :return: (角色目录, 图片路径, 显示名称, 别名列表)
    逻辑：
    1. 遍历角色根目录的所有子目录
    2. 随机选择有效图片文件
    3. 排除JSON配置文件本身
    """
    if not CHARACTER_IMAGE_DIR.exists():
        return None, None, None, None

    character_dirs = [d for d in CHARACTER_IMAGE_DIR.iterdir() if d.is_dir()]
    if not character_dirs:
        return None, None, None, None

    character_dir = random.choice(character_dirs)

    # 查找文件夹中的图片文件（排除JSON）
    images = [f for f in character_dir.glob("*")
              if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
              and not f.name.endswith(".json")]

    if not images:
        return None, None, None, None

    image_path = random.choice(images)
    display_name, aliases = get_character_info(character_dir)
    return character_dir, image_path, display_name, aliases


def select_random_music_image() -> tuple[Path | None, Path | None, str | None, list[str] | None]:
    """
    随机选择歌曲和曲绘图片
    每首歌只有一个曲绘图片
    """
    if not MUSIC_IMAGE_DIR.exists():
        return None, None, None, None

    music_dirs = [d for d in MUSIC_IMAGE_DIR.iterdir() if d.is_dir()]
    if not music_dirs:
        return None, None, None, None

    music_dir = random.choice(music_dirs)

    # 不同点2
    # 查找文件夹中的图片文件（排除JSON）
    images = [f for f in music_dir.glob("*")
              if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
              and not f.name.endswith(".json")]

    if not images:
        return None, None, None, None

    # 疑问点：image_path = images[0]改成image_path = random.choice(images)是否可行
    # 每首歌只取一个曲绘（取找到的第一个）
    # image_path = images[0]
    image_path = random.choice(images)
    display_name, aliases = get_music_info(music_dir)
    return music_dir, image_path, display_name, aliases


# 生成裁剪图片
def crop_character_image(image_path: Path) -> Path:
    """
    生成随机裁剪图片
    :param image_path: 原始图片路径
    :return: 临时裁剪图片路径
    特点：
    - 固定裁剪200x200像素区域
    - 自动适配图片尺寸
    - 保存为PNG格式
    """
    img = Image.open(image_path)
    w, h = img.size

    # 定义裁剪区域的固定像素大小
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
    """生成随机裁剪图片（100x100像素），可更改"""
    img = Image.open(image_path)
    w, h = img.size

    # 定义裁剪区域的固定像素大小
    crop_width, crop_height = 100, 100

    if crop_width > w or crop_height > h:
        crop_width = min(crop_width, w)
        crop_height = min(crop_height, h)

    # 不同点3（可忽略
    left = random.randint(0, w - crop_width)
    upper = random.randint(0, h - crop_height)

    cropped = img.crop((left, upper, left + crop_width, upper + crop_height))

    temp_file = TEMP_DIR / f"music_{time.time_ns()}.png"
    cropped.save(temp_file)
    return temp_file



# --------------------------
# 定时任务
# --------------------------
# 使用apscheduler插件实现定时任务
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("interval", minutes=10)
def cleanup_temp_files():
    """清理临时目录（每10分钟执行）"""
    for file in TEMP_DIR.glob("*"):
        if file.is_file():
            # 不同点4（可忽略
            try:
                file.unlink()
            except:
                pass


# @scheduler.scheduled_job("interval", seconds=10, misfire_grace_time=30, coalesce=True)
@scheduler.scheduled_job("interval", seconds=10)
async def cleanup_sessions():
    """
    会话清理任务（每10秒执行）
    功能：
    1. 清理超时会话并公布答案
    2. 移除过期的答案缓存
    3. 删除临时裁剪图片
    """
    current_time = time.time()

    # 清理过期会话
    # 不同点5，优化原因：直接列表推导式在会话量大时可能消耗更多内存，迭代方式更节省资源。
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

            # 不同点6，增加了文件删除的异常处理
            finally:
                if session["cropped_image"].exists():
                    try:
                        session["cropped_image"].unlink()
                    except:
                        pass

    for key in expired_keys:
        sessions.pop(key, None)

    # 清理过期的答案缓存
    # 不同点7，使用更安全的pop方法，避免KeyError异常导致任务中断。
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
    """
    检查是否是有效的回复消息
    有效条件：
    1. 回复了本游戏的机器人消息
    2. 在有效会话期内或答案保留期内
    """
    if not event.reply:
        return False

    session_key = (event.user_id, event.group_id)
    if session_key in sessions:
        return event.reply.message_id == sessions[session_key]["bot_msg_id"]

    return event.reply.message_id in message_id_to_answer



# --------------------------
# 事件响应器
# --------------------------
guessplay_character = on_fullmatch("猜卡面")
guessplay_music = on_fullmatch("猜曲绘")
reply_matcher = on_message(rule=Rule(check_reply), block=True)



# --------------------------
# 事件处理
# --------------------------
@guessplay_character.handle()
async def handle_trigger(bot: Bot, event: GroupMessageEvent):
    """处理猜卡面游戏触发"""
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        # await trigger_matcher.finish("❌ 该群未获得使用权限，请联系管理员")
        return

    # 黑名单检查（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await trigger_matcher.finish(MessageSegment.reply(event.message_id) +
        #                                MessageSegment.text("您已被禁用Ena-bot"))
        return

    # 使用限制检查
    user_id = event.get_user_id()
    if not (await check_guessplay_usage(user_id)):
        await guessplay_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天游戏次数到达上限了，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    if session_key in sessions:
        if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
            del sessions[session_key]
        else:
            await guessplay_character.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
            )

    character_dir, image_path, display_name, aliases = select_random_character_image()
    if not all([character_dir, image_path, display_name, aliases]):
        await guessplay_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
        )

    try:
        cropped_path = crop_character_image(image_path)

    except Exception as e:
        nonebot.logger.error(f"角色图片处理失败：{e}")
        await guessplay_character.finish(
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
        await guessplay_character.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("猜卡面游戏初始化失败，请稍后再试")
        )


@guessplay_music.handle()
async def handle_trigger(bot: Bot, event: GroupMessageEvent):
    """处理猜曲绘游戏触发"""
    # 黑白名单检查
    if not await check_group_whitelist(event.group_id):
        return

    if await check_user_blacklist(event.user_id):
        return

    # 使用限制检查
    user_id = event.get_user_id()
    if not (await check_guessplay_usage(user_id)):
        await guessplay_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("今天的游戏次数已达上限，明天再来吧")
        )

    session_key = (event.user_id, event.group_id)

    # 清理过期会话
    if session_key in sessions:
        if time.time() - sessions[session_key]["timestamp"] > TIMEOUT:
            del sessions[session_key]
        else:
            await guessplay_music.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("您有一个进行中的游戏，请先完成或等待超时。")
            )

    # 随机选择歌曲
    song_dir, image_path, display_name, aliases = select_random_music_image()
    if not all([song_dir, image_path, display_name, aliases]):
        await guessplay_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("暂时无法开始游戏，请联系开发者检查资源")
        )

    # 裁剪图片
    try:
        cropped_path = crop_music_image(image_path)

    except Exception as e:
        nonebot.logger.error(f"曲绘图片处理失败：{e}")
        await guessplay_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("曲绘图片处理失败，请稍后再试")
        )

    # 发送游戏开始消息
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
        await guessplay_music.finish(
            MessageSegment.reply(event.message_id) + \
            MessageSegment.text("游戏初始化失败，请稍后再试")
        )


@reply_matcher.handle()
async def handle_reply(event: GroupMessageEvent):
    """处理用户回复"""
    reply_msg_id = event.reply.message_id
    session_key = (event.user_id, event.group_id)

    # 不同点8，提前获取用户输入
    user_input = event.get_plaintext().strip().lower()

    # 处理进行中的会话
    if session_key in sessions:
        session = sessions[session_key]
        current_time = time.time()

        # 超时处理
        if current_time - session["timestamp"] > TIMEOUT:
            del sessions[session_key]
            reply_msg = MessageSegment.reply(event.message_id) + \
                        MessageSegment.text("回答超时！正确答案是：") + \
                        MessageSegment.text(session["display_name"]) + \
                        MessageSegment.image(session["original_image"])
            await reply_matcher.finish(reply_msg)

        # 主动退出
        # if user_input == "结束猜曲绘":
        if user_input == f"结束猜{session['game_type']}":
            del sessions[session_key]
            await reply_matcher.finish(
                MessageSegment.reply(event.message_id) + \
                MessageSegment.text("已退出当前游戏")
            )

        # 验证答案
        is_correct = user_input in session["aliases"]

        # 构造回复消息
        reply_msg = MessageSegment.reply(event.message_id)

        # 不同点9（可忽略
        if is_correct:
            reply_msg += MessageSegment.text("锵锵！猜对啦")
            #reply_msg += MessageSegment.text("🎉 猜对啦！正确答案：") + \
            #             MessageSegment.text(session["display_name"])
        else:
            reply_msg += MessageSegment.text(f"猜错了哦，正确答案是：{session['display_name']}")

        reply_msg += MessageSegment.image(session["original_image"])
        await reply_matcher.send(reply_msg) # send改finish存疑

        # 清理会话
        del sessions[session_key]
        if session["cropped_image"].exists():
            # 不同点10，添加异常处理
            try:
                session["cropped_image"].unlink()
            except:
                pass
        return

    # 处理已超时的答案查询
    if reply_msg_id in message_id_to_answer:
        data = message_id_to_answer[reply_msg_id]
        reply_msg = MessageSegment.reply(event.message_id) + \
                    MessageSegment.text("游戏已超时，正确答案是：") + \
                    MessageSegment.text(data["display_name"]) + \
                    MessageSegment.image(data["original_image"])
        await reply_matcher.finish(reply_msg)

    await reply_matcher.finish()

"""
QQ群聊猜卡面、猜曲绘游戏插件

功能说明：
1. 用户发送触发关键词开始游戏
2. 机器人随机选择图片并生成指定规格像素的随机裁剪图
3. 用户通过回复消息猜测名称（支持别名）
4. 包含超时机制（默认30秒）和主动退出功能
5. 回答后显示完整原图及正确答案
6. 自动清理临时文件和过期会话

主要特性：
- 多角色、歌曲支持：通过目录结构自动加载角色卡面、曲绘
- 别名系统：支持通过JSON文件配置角色和歌曲别名
- 安全机制：临时文件定期清理，防止存储膨胀
- 会话管理：支持同一群组多用户独立游戏
- 超时处理：自动结算未回答的游戏

目录结构要求：
├─ characters/
│  ├─ 角色1文件夹/
│  │  ├─ 卡面图片文件（支持多种格式）
│  │  └─ 角色名称.json（可选，配置别名）
│  ├─ 角色2文件夹/
│  │  ├─ 卡面图片文件
│  │  └─ 角色名称.json
│  └─ ...
└─ musics/
   ├─ 歌曲1文件夹/
   │  ├─ 曲绘图片文件（支持多种格式）
   │  └─ 歌曲名称.json（可选，配置别名）
   ├─ 歌曲2文件夹/
   │  ├─ 曲绘图片文件
   │  └─ 歌曲名称.json
   └─ ...

JSON配置示例：
{
    "display_name": "显示名称",
    "aliases": ["别名1", "别名2"]
}

使用流程：
1. 用户发送"猜卡面"、"猜曲绘"触发游戏
2. 机器人回复裁剪后的图片
3. 用户引用机器人消息发送猜测答案
4. 机器人验证答案并公布结果

定时任务：
- 每10分钟清理临时图片文件
- 每10秒检查过期会话（超时+10秒缓冲）
"""