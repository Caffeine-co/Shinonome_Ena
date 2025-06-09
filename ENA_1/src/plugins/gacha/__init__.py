import os
import random
import logging
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from nonebot import on_fullmatch
from nonebot.rule import Rule
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot import require
from PIL import Image

logger = logging.getLogger(__name__)

WHITELIST_PATH = Path("***/ENA_1/src/plugins/group_whitelist.json")
BLACKLIST_PATH = Path("***/ENA_1/src/plugins/user_blacklist.json")

DATA_FILE = Path(__file__).parent / "usage_data_gacha.json"
MAX_DAILY_LIMIT = 50
EXEMPT_USER_ID = "Your_qq_number"

BG_PATH = Path(__file__).parent / "gacha_resources/背景图"

ORD_FOUR_STAR_PATH = Path(__file__).parent / "gacha_resources/普池/四星卡"
LIM_FOUR_STAR_PATH = Path(__file__).parent / "gacha_resources/限定池/四星卡"

ORD_THREE_STAR_PATH = Path(__file__).parent / "gacha_resources/普池/三星卡"
LIM_THREE_STAR_PATH = Path(__file__).parent / "gacha_resources/限定池/三星卡"

ORD_TWO_STAR_PATH = Path(__file__).parent / "gacha_resources/普池/二星卡"
LIM_TWO_STAR_PATH = Path(__file__).parent / "gacha_resources/限定池/二星卡"

TEMP_PATH = Path(__file__).parent / "temp"

TEMP_PATH.mkdir(parents=True, exist_ok=True)


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
            blacklist = json.loads(await f.read())
            return user_id in blacklist
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return True
    except Exception as e:
        return True

async def check_usage_ten(user_id: str):
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
        new_count = 10
        update_data = {"date": current_date, "count": new_count}
    else:
        new_count = record["count"] + 10
        update_data = {"date": current_date, "count": new_count}

    if new_count > MAX_DAILY_LIMIT:
        return False

    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True

async def check_usage_one(user_id: str):
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

PROBABILITY = {
    "4star": 0.03,
    "3star": 0.07,
    "2star": 0.90
}

BG_SIZE = (1024, 630)
CARD_SIZE_SINGLE = (200, 200)
CARD_SIZE_MULTI = (150, 150)

GRID_LAYOUT = {
    0: (37, 140), 1: (237, 140), 2: (437, 140), 3: (637, 140), 4: (837, 140),
    5: (37, 340), 6: (237, 340), 7: (437, 340), 8: (637, 340), 9: (837, 340)
}

scheduler = require("nonebot_plugin_apscheduler").scheduler

@scheduler.scheduled_job("cron", minute="*/5")
async def clean_temp_folder():
    try:
        for file in TEMP_PATH.glob("*"):
            if file.is_file():
                file.unlink()
        logger.info(f"临时文件夹已清理：{TEMP_PATH}")
    except Exception as e:
        logger.error(f"清理临时文件夹失败：{str(e)}")

gacha_ord_one = on_fullmatch("pjsk单抽")
gacha_ord_ten = on_fullmatch("pjsk十连")
gacha_lim_one = on_fullmatch("pjsk限定单抽")
gacha_lim_ten = on_fullmatch("pjsk限定十连")

async def get_random_ord_card() -> Tuple[Path, str]:
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


async def generate_one_gacha_ord_image(card_path: Path) -> Path:
    try:
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        card = Image.open(card_path).resize(CARD_SIZE_SINGLE)
        x = (BG_SIZE[0] - CARD_SIZE_SINGLE[0]) // 2
        y = (BG_SIZE[1] - CARD_SIZE_SINGLE[1]) // 2
        bg_image.paste(card, (x, y))

        output_path = TEMP_PATH / f"one_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"单抽图片合成失败: {str(e)}") from e


async def generate_ten_gacha_ord_image(card_paths: List[Path]) -> Path:
    try:
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        for idx, card_path in enumerate(card_paths):
            card = Image.open(card_path).resize(CARD_SIZE_MULTI)
            bg_image.paste(card, GRID_LAYOUT[idx])

        output_path = TEMP_PATH / f"ten_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"十连图片合成失败: {str(e)}") from e


async def generate_one_gacha_lim_image(card_path: Path) -> Path:
    try:
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        card = Image.open(card_path).resize(CARD_SIZE_SINGLE)
        x = (BG_SIZE[0] - CARD_SIZE_SINGLE[0]) // 2
        y = (BG_SIZE[1] - CARD_SIZE_SINGLE[1]) // 2
        bg_image.paste(card, (x, y))

        output_path = TEMP_PATH / f"one_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"单抽图片合成失败: {str(e)}") from e


async def generate_ten_gacha_lim_image(card_paths: List[Path]) -> Path:
    try:
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        for idx, card_path in enumerate(card_paths):
            card = Image.open(card_path).resize(CARD_SIZE_MULTI)
            bg_image.paste(card, GRID_LAYOUT[idx])

        output_path = TEMP_PATH / f"ten_{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"十连图片合成失败: {str(e)}") from e


async def build_message(event: GroupMessageEvent, image_path: Path, results: List[Tuple[Path, str]]) -> Message:
    star_count = {"4star": 0, "3star": 0, "2star": 0}
    for _, star in results:
        star_count[star] += 1

    text = (
        f"===招募结果===\n"
        f"★★★★：{star_count['4star']}\n"
        f"★★★：{star_count['3star']}\n"
        f"★★：{star_count['2star']}"
    )

    return Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(text + "\n"),
        MessageSegment.image(image_path)
    ])

@gacha_ord_one.handle()
async def handle_gacha_ord_one(event: GroupMessageEvent):
    try:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        user_id = event.get_user_id()
        if not (await check_usage_one(user_id)):
            await gacha_ord_one.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        card_path, star = await get_random_ord_card()

        image_path = await generate_one_gacha_ord_image(card_path)

        msg = await build_message(event, image_path, [(card_path, star)])
        await gacha_ord_one.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("单抽处理失败")
        await gacha_ord_one.finish(f"单抽失败：{str(e)}")


@gacha_ord_ten.handle()
async def handle_gacha_ord_ten(event: GroupMessageEvent):
    try:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        user_id = event.get_user_id()
        if not (await check_usage_ten(user_id)):
            await gacha_ord_ten.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        results = []
        card_paths = []
        has_high_star = False

        for _ in range(9):
            card, star = await get_random_ord_card()
            results.append((card, star))
            card_paths.append(card)
            if star in ("3star", "4star"):
                has_high_star = True

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

        image_path = await generate_ten_gacha_ord_image(card_paths)

        msg = await build_message(event, image_path, results)
        await gacha_ord_ten.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("十连处理失败")
        await gacha_ord_ten.finish(f"十连失败：{str(e)}")


@gacha_lim_one.handle()
async def handle_gacha_lim_one(event: GroupMessageEvent):
    try:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        user_id = event.get_user_id()
        if not (await check_usage_one(user_id)):
            await gacha_lim_one.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        card_path, star = await get_random_lim_card()

        image_path = await generate_one_gacha_lim_image(card_path)

        msg = await build_message(event, image_path, [(card_path, star)])
        await gacha_lim_one.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("单抽处理失败")
        await gacha_lim_one.finish(f"单抽失败：{str(e)}")


@gacha_lim_ten.handle()
async def handle_gacha_lim_ten(event: GroupMessageEvent):
    try:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        user_id = event.get_user_id()
        if not (await check_usage_ten(user_id)):
            await gacha_lim_ten.finish(
                MessageSegment.reply(event.message_id) + "今天抽卡次数达到上限了，明天再来吧"
            )

        results = []
        card_paths = []
        has_high_star = False

        for _ in range(9):
            card, star = await get_random_lim_card()
            results.append((card, star))
            card_paths.append(card)
            if star in ("3star", "4star"):
                has_high_star = True

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

        image_path = await generate_ten_gacha_lim_image(card_paths)

        msg = await build_message(event, image_path, results)
        await gacha_lim_ten.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception("十连处理失败")
        await gacha_lim_ten.finish(f"十连失败：{str(e)}")
