# --------------------------
# 导入区域
# --------------------------
import random
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from nonebot import on_fullmatch, on_regex
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot import require
from PIL import Image

from ._430_ import check_group_whitelist, check_user_blacklist, check_gacha_usage_one, check_gacha_usage_ten



# --------------------------
# 插件元信息配置
# --------------------------
__plugin_meta__ = PluginMetadata(
    name="群聊抽卡模拟器",
    description="QQ群聊抽卡模拟插件（严格匹配版）",
    usage="发送【pjsk单抽】或【pjsk十连】进行抽卡",
    type="application",
    homepage="https://github.com/yourname/yourrepo",
    extra={"version": "1.2.0"},
)



# --------------------------
# 日志配置
# --------------------------
logger = logging.getLogger(__name__)



# --------------------------
# 路径与资源配置区域
# --------------------------

BG_PATH = Path(__file__).parent / "resources/J/gacha_resources/背景图"

ORD_FOUR_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/普池/四星卡"
LIM_FOUR_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/限定池/四星卡"

ORD_THREE_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/普池/三星卡"
LIM_THREE_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/限定池/三星卡"

ORD_TWO_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/普池/二星卡"
LIM_TWO_STAR_PATH = Path(__file__).parent / "resources/J/gacha_resources/限定池/二星卡"

BIRTH_PATH = Path(__file__).parent / "resources/J/gacha_resources/生日池"

TEMP_PATH = Path(__file__).parent / "resources/J/temp"

# 创建临时目录（如果不存在）
TEMP_PATH.mkdir(parents=True, exist_ok=True)



# --------------------------
# 概率配置（可自定义调整）
# --------------------------
# 一般池概率
PROBABILITY = {
    "4star": 0.03,  # 4星概率2%
    "3star": 0.07,  # 3星概率8%
    "2star": 0.90  # 2星概率90%
}


# 生日池概率
BIRTH_PROBABILITY = {
    "4star": 0.03,  # 生日卡概率6% (高于普通池)
    "3star": 0.07,  # 三星概率15%
    "2star": 0.90  # 二星概率79%
}



# --------------------------
# 图像尺寸配置（根据实际图片尺寸调整）
# --------------------------
BG_SIZE = (1024, 630)  # 背景图尺寸
CARD_SIZE_SINGLE = (200, 200)  # 单抽卡片尺寸
CARD_SIZE_MULTI = (150, 150)  # 十连卡片尺寸

# 十连抽布局坐标（两行五列布局）
GRID_LAYOUT = {
    0: (37, 140), 1: (237, 140), 2: (437, 140), 3: (637, 140), 4: (837, 140),
    5: (37, 340), 6: (237, 340), 7: (437, 340), 8: (637, 340), 9: (837, 340)
}



# --------------------------
# 定时清理任务（清理临时文件夹）
# --------------------------
scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job("cron", minute="*/5")  # 每小时触发一次，可根据实际需求调整清理周期，例如每30分钟（minute="*/30"）、每小时（hour="*"）
async def clean_temp_folder():
    """每小时清理临时图片文件"""
    try:
        for file in TEMP_PATH.glob("*"):
            if file.is_file():
                file.unlink()
        logger.info(f"临时文件夹已清理：{TEMP_PATH}")
    except Exception as e:
        logger.error(f"清理临时文件夹失败：{str(e)}")



# --------------------------
# 事件响应器
# --------------------------
gacha_ord_one = on_fullmatch("pjsk单抽")
gacha_ord_ten = on_fullmatch("pjsk十连")
gacha_lim_one = on_fullmatch("pjsk限定单抽")
gacha_lim_ten = on_fullmatch("pjsk限定十连")
gacha_birth_one = on_regex(r"^pjsk生日单抽\s*(\S+)$")  # 增加分组捕获
gacha_birth_ten = on_regex(r"^pjsk生日十连\s*(\S+)$")  # 增加分组捕获


# --------------------------
# 函数定义
# --------------------------
# 卡牌选取函数
async def get_random_ord_card() -> Tuple[Path, str]:
    """随机获取普池卡牌
    Returns:
        Tuple[Path, str]: (卡牌路径, 星级)
    """
    rand = random.random()
    if rand < PROBABILITY["4star"]:
        star = "4star"
        path = ORD_FOUR_STAR_PATH
    elif rand < PROBABILITY["4star"] + PROBABILITY["3star"]:
        star = "3star"
        path = ORD_THREE_STAR_PATH
    else:
        star = "2star"
        path = ORD_TWO_STAR_PATH

    cards = list(path.glob("*.*"))
    if not cards:
        raise FileNotFoundError(f"卡牌图片缺失：{path}")
    return random.choice(cards), star


async def get_random_lim_card() -> Tuple[Path, str]:
    """随机获取限定池卡牌
    Returns:
        Tuple[Path, str]: (卡牌路径, 星级)
    """
    rand = random.random()
    if rand < PROBABILITY["4star"]:
        star = "4star"
        path = LIM_FOUR_STAR_PATH
    elif rand < PROBABILITY["4star"] + PROBABILITY["3star"]:
        star = "3star"
        path = LIM_THREE_STAR_PATH
    else:
        star = "2star"
        path = LIM_TWO_STAR_PATH

    cards = list(path.glob("*.*"))
    if not cards:
        raise FileNotFoundError(f"卡牌图片缺失：{path}")
    return random.choice(cards), star


async def get_random_birth_card(character: str) -> Tuple[Path, str]:
    """随机获取生日池卡牌
    Args:
        character: 角色名称
    Returns:
        Tuple[Path, str]: (卡牌路径, 星级)
    """
    # 构建角色路径
    char_path = BIRTH_PATH / character

    # 验证角色路径是否存在
    if not char_path.exists() or not char_path.is_dir():
        available_chars = ", ".join([d.name for d in BIRTH_PATH.iterdir() if d.is_dir()])
        raise ValueError(
            f"角色名 '{character}' 不支持呢，\n可用角色名: {available_chars}"
            )

    # 根据概率抽取星级
    rand = random.random()
    if rand < BIRTH_PROBABILITY["4star"]:
        star = "4star"
        path = char_path / "生日卡"
    elif rand < BIRTH_PROBABILITY["4star"] + BIRTH_PROBABILITY["3star"]:
        star = "3star"
        path = char_path / "三星卡"
    else:
        star = "2star"
        path = char_path / "二星卡"

    # 检查卡牌文件
    cards = list(path.glob("*.*"))
    if not cards:
        raise FileNotFoundError(f"角色 '{character}' 的{star}卡牌图片缺失：{path}")

    return random.choice(cards), star


# 图片生成函数
async def generate_one_gacha_image(card_path: Path) -> Path:
    """生成单抽结果图片
    Args:
        card_path: 卡牌路径
    Returns:
        生成图片的保存路径
    """
    try:
        # 随机选择背景图并调整尺寸
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        # 单抽模式居中布局
        card = Image.open(card_path).resize(CARD_SIZE_SINGLE)
        x = (BG_SIZE[0] - CARD_SIZE_SINGLE[0]) // 2
        y = (BG_SIZE[1] - CARD_SIZE_SINGLE[1]) // 2
        bg_image.paste(card, (x, y))

        # 保存临时文件
        output_path = TEMP_PATH / f"one_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"单抽图片合成失败: {str(e)}") from e


async def generate_ten_gacha_image(card_paths: List[Path]) -> Path:
    """生成十连结果图片
    Args:
        card_paths: 卡牌路径列表
    Returns:
        生成图片的保存路径
    """
    try:
        # 随机选择背景图并调整尺寸
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        # 十连模式布局
        for idx, card_path in enumerate(card_paths):
            card = Image.open(card_path).resize(CARD_SIZE_MULTI)
            bg_image.paste(card, GRID_LAYOUT[idx])

        # 保存临时文件
        output_path = TEMP_PATH / f"ten_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"十连图片合成失败: {str(e)}") from e


# 消息样式构建函数
async def build_ord_message(event: GroupMessageEvent, image_path: Path, results: List[Tuple[Path, str]]) -> Message:
    """构建普池返回消息
    Args:
        event: 群消息事件
        image_path: 图片路径
        results: 抽卡结果列表
    Returns:
        包含引用回复和图片的消息
    """
    # 统计各星级数量
    star_count = {"4star": 0, "3star": 0, "2star": 0}
    for _, star in results:
        star_count[star] += 1

    # 构建消息内容
    text = (
        f"🎨招募结果🎨\n"
        f"⭐⭐⭐⭐：{star_count['4star']}\n"
        f"⭐⭐⭐：{star_count['3star']}\n"
        f"⭐⭐：{star_count['2star']}"
    )

    return Message([
        MessageSegment.reply(event.message_id),  # 引用原消息
        MessageSegment.text(text + "\n"),
        MessageSegment.image(image_path)  # 添加结果图片
    ])


async def build_lim_message(event: GroupMessageEvent, image_path: Path, results: List[Tuple[Path, str]]) -> Message:
    """构建限定池返回消息
    Args:
        event: 群消息事件
        image_path: 图片路径
        results: 抽卡结果列表
    Returns:
        包含引用回复和图片的消息
    """
    # 统计各星级数量
    star_count = {"4star": 0, "3star": 0, "2star": 0}
    for _, star in results:
        star_count[star] += 1

    # 构建消息内容
    text = (
        f"🎨招募结果🎨\n"
        f"⭐⭐⭐⭐：{star_count['4star']}\n"
        f"⭐⭐⭐：{star_count['3star']}\n"
        f"⭐⭐：{star_count['2star']}"
    )

    return Message([
        MessageSegment.reply(event.message_id),  # 引用原消息
        MessageSegment.text(text + "\n"),
        MessageSegment.image(image_path)  # 添加结果图片
    ])


async def build_birth_message(event: GroupMessageEvent, image_path: Path, results: List[Tuple[Path, str]]) -> Message:
    """构建生日池返回消息
    Args:
        event: 群消息事件
        image_path: 图片路径
        results: 抽卡结果列表
    Returns:
        包含引用回复和图片的消息
    """
    # 统计各星级数量
    star_count = {"4star": 0, "3star": 0, "2star": 0}
    for _, star in results:
        star_count[star] += 1

    # 构建消息内容
    text = (
        f"🎨招募结果🎨\n"
        f"🎀：{star_count['4star']}\n"
        f"⭐⭐⭐：{star_count['3star']}\n"
        f"⭐⭐：{star_count['2star']}"
    )

    return Message([
        MessageSegment.reply(event.message_id),  # 引用原消息
        MessageSegment.text(text + "\n"),
        MessageSegment.image(image_path)  # 添加结果图片
    ])


# --------------------------
# 事件处理
# --------------------------
@gacha_ord_one.handle()
async def handle_gacha_ord_one(event: GroupMessageEvent):
    """处理单抽命令"""
    try:
        # 白名单检查
        if not await check_group_whitelist(event.group_id):
            #   await gacha_handler.finish("❌ 该群未获得使用权限，请联系管理员")
            return

        # 黑名单检查（紧随白名单之后）
        if await check_user_blacklist(event.user_id):
            #   await gacha_handler.finish(Message([
            #       MessageSegment.reply(event.message_id),
            #       MessageSegment.text("您已被禁用Ena-bot")
            #   ]))
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_one(user_id)):
            await gacha_ord_one.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        # 获取单抽结果
        card_path, star = await get_random_ord_card()

        # 生成结果图片
        image_path = await generate_one_gacha_image(card_path)

        # 构建返回消息
        msg = await build_ord_message(event, image_path, [(card_path, star)])
        await gacha_ord_one.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("单抽处理失败")
        await gacha_ord_one.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )


@gacha_ord_ten.handle()
async def handle_gacha_ord_ten(event: GroupMessageEvent):
    """处理十连命令"""
    try:
        # 白名单检查
        if not await check_group_whitelist(event.group_id):
            return

        # 黑名单检查（紧随白名单之后）
        if await check_user_blacklist(event.user_id):
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_ten(user_id)):
            await gacha_ord_ten.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        results = []
        card_paths = []
        has_high_star = False

        # 前9次抽取
        for _ in range(9):
            card, star = await get_random_ord_card()
            results.append((card, star))
            card_paths.append(card)
            if star in ("3star", "4star"):
                has_high_star = True

        # 第10次保底
        if not has_high_star:
            total_high_prob = PROBABILITY["3star"] + PROBABILITY["4star"]
            rand = random.uniform(0, total_high_prob)
            star = "4star" if rand < PROBABILITY["4star"] else "3star"
            path = ORD_FOUR_STAR_PATH if star == "4star" else ORD_THREE_STAR_PATH
            cards = list(path.glob("*.*"))
            if not cards:
                raise FileNotFoundError(f"找不到{star}卡牌图片")
            card = random.choice(cards)
            results.append((card, star))
            card_paths.append(card)
        else:
            card, star = await get_random_ord_card()
            results.append((card, star))
            card_paths.append(card)

        # 生成十连结果图片
        image_path = await generate_ten_gacha_image(card_paths)

        # 构建返回消息
        msg = await build_ord_message(event, image_path, results)
        await gacha_ord_ten.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("十连处理失败")
        await gacha_ord_ten.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )


@gacha_lim_one.handle()
async def handle_gacha_lim_one(event: GroupMessageEvent):
    """处理限定单抽命令"""
    try:
        # 白名单检查
        if not await check_group_whitelist(event.group_id):
            return

        # 黑名单检查（紧随白名单之后）
        if await check_user_blacklist(event.user_id):
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_one(user_id)):
            await gacha_lim_one.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        # 获取单抽结果
        card_path, star = await get_random_lim_card()

        # 生成结果图片
        image_path = await generate_one_gacha_image(card_path)

        # 构建返回消息
        msg = await build_lim_message(event, image_path, [(card_path, star)])
        await gacha_lim_one.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("单抽处理失败")
        await gacha_lim_one.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )


@gacha_lim_ten.handle()
async def handle_gacha_lim_ten(event: GroupMessageEvent):
    """处理限定十连命令"""
    try:
        # 白名单检查
        if not await check_group_whitelist(event.group_id):
            return

        # 黑名单检查（紧随白名单之后）
        if await check_user_blacklist(event.user_id):
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_ten(user_id)):
            await gacha_lim_ten.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        results = []
        card_paths = []
        has_high_star = False

        # 前9次抽取
        for _ in range(9):
            card, star = await get_random_lim_card()
            results.append((card, star))
            card_paths.append(card)
            if star in ("3star", "4star"):
                has_high_star = True

        # 第10次保底
        if not has_high_star:
            total_high_prob = PROBABILITY["3star"] + PROBABILITY["4star"]
            rand = random.uniform(0, total_high_prob)
            star = "4star" if rand < PROBABILITY["4star"] else "3star"
            path = ORD_FOUR_STAR_PATH if star == "4star" else ORD_THREE_STAR_PATH
            cards = list(path.glob("*.*"))
            if not cards:
                raise FileNotFoundError(f"找不到{star}卡牌图片")
            card = random.choice(cards)
            results.append((card, star))
            card_paths.append(card)
        else:
            card, star = await get_random_lim_card()
            results.append((card, star))
            card_paths.append(card)

        # 生成十连结果图片
        image_path = await generate_ten_gacha_image(card_paths)

        # 构建返回消息
        msg = await build_lim_message(event, image_path, results)
        await gacha_lim_ten.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("十连处理失败")
        await gacha_lim_ten.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )


@gacha_birth_one.handle()
async def handle_gacha_birth_one(event: GroupMessageEvent):
    """处理生日单抽命令"""
    try:
        # 从正则匹配中直接提取角色名
        # match = event.get_plaintext().strip()
        # 提取第一个捕获组内容
        # character = match.group(1)

        # 使用正则分组提取角色名
        msg_text = event.get_plaintext().strip()
        match = re.match(r"^pjsk生日单抽\s*(\S.*?)$", msg_text)

        # if not match:
        #    await gacha_birth_one.finish(
        #        MessageSegment.reply(event.message_id) + "你要抽谁的生日卡呢"
        #    )

        # 提取第一个捕获组内容
        character = match.group(1).strip()

        # 权限检查
        if not await check_group_whitelist(event.group_id):
            return
        if await check_user_blacklist(event.user_id):
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_one(user_id)):
            await gacha_birth_one.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        # 获取抽卡结果
        card_path, star = await get_random_birth_card(character)

        # 生成结果图片
        image_path = await generate_one_gacha_image(card_path)

        # 构建返回消息
        msg = await build_birth_message(event, image_path, [(card_path, star)])
        await gacha_birth_one.finish(msg)

    except ValueError as ve:
        await gacha_birth_one.finish(
            MessageSegment.reply(event.message_id) + f"{str(ve)}"
        )
    except FinishedException:
        pass
    except Exception as e:
        logger.exception("生日单抽处理失败")
        await gacha_birth_one.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )


@gacha_birth_ten.handle()
async def handle_gacha_birth_ten(event: GroupMessageEvent):
    """处理生日十连命令"""
    try:
        # 从正则匹配中直接提取角色名
        # match = event.get_plaintext().strip()
        # 提取第一个捕获组内容
        # character = match.group(1)

        # 使用正则分组提取角色名
        msg_text = event.get_plaintext().strip()
        match = re.match(r"^pjsk生日十连\s*(\S.*?)$", msg_text)

        # if not match:
        #    await gacha_birth_ten.finish(
        #        MessageSegment.reply(event.message_id) + "你要抽谁的生日卡呢"
        #    )

        # 提取第一个捕获组内容
        character = match.group(1).strip()

        # 权限检查
        if not await check_group_whitelist(event.group_id):
            return
        if await check_user_blacklist(event.user_id):
            return

        # 使用限制检查
        user_id = event.get_user_id()
        if not (await check_gacha_usage_ten(user_id)):
            await gacha_birth_ten.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        results = []
        card_paths = []
        has_high_star = False

        # 前9次抽取
        for _ in range(9):
            card, star = await get_random_birth_card(character)
            results.append((card, star))
            card_paths.append(card)
            if star in ("3star", "4star"):
                has_high_star = True

        # 第10次保底机制
        if not has_high_star:
            # 保底必出3星以上卡
            total_high_prob = BIRTH_PROBABILITY["3star"] + BIRTH_PROBABILITY["4star"]
            rand = random.uniform(0, total_high_prob)
            star = "4star" if rand < PROBABILITY["4star"] else "3star"

            char_path = BIRTH_PATH / character
            # path = char_path / "三星卡"
            path = char_path / "生日卡" if star == "4star" else char_path /"三星卡"
            cards = list(path.glob("*.*"))
            if not cards:
                raise FileNotFoundError(f"角色 '{character}' 卡牌缺失")
            card = random.choice(cards)
            results.append((card, star))
            card_paths.append(card)
        else:
            # 正常抽取
            card, star = await get_random_birth_card(character)
            results.append((card, star))
            card_paths.append(card)

        # 生成十连结果图片
        image_path = await generate_ten_gacha_image(card_paths)

        # 构建返回消息
        msg = await build_birth_message(event, image_path, results)
        await gacha_birth_ten.finish(msg)

    except ValueError as ve:
        await gacha_birth_ten.finish(
            MessageSegment.reply(event.message_id) + f"{str(ve)}"
        )
    except FinishedException:
        pass
    except Exception as e:
        logger.exception("生日十连处理失败")
        await gacha_birth_ten.finish(
            MessageSegment.reply(event.message_id) + f"事件处理失败：{str(e)}"
        )