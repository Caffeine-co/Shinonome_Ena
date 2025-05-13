import os
import random
import logging
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from nonebot import on_message
from nonebot.rule import Rule
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot import require
from PIL import Image

logger = logging.getLogger(__name__)

WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"
BG_PATH = Path("Your_path/ENA_1/src/plugins/gacha_resources/背景图")
FOUR_STAR_PATH = Path("Your_path/ENA_1/src/plugins/gacha_resources/普池/四星卡")
THREE_STAR_PATH = Path("Your_path/ENA_1/src/plugins/gacha_resources/普池/三星卡")
TWO_STAR_PATH = Path("Your_path/ENA_1/src/plugins/gacha_resources/普池/二星卡")
TEMP_PATH = Path("Your_path/ENA_1/src/plugins/gacha_resources/temp")

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

PROBABILITY = {
    "4star": 0.02,
    "3star": 0.08,
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

def is_strict_gacha_command(event: GroupMessageEvent) -> bool:
    msg = event.get_plaintext()
    return msg in {"pjsk单抽", "pjsk十连"}

gacha_handler = on_message(
    rule=Rule(is_strict_gacha_command),
    block=True
)

async def get_random_card() -> Tuple[Path, str]:
    rand = random.random()
    if rand < PROBABILITY["4star"]:
        star = "4star"
        path = FOUR_STAR_PATH
    elif rand < PROBABILITY["4star"] + PROBABILITY["3star"]:
        star = "3star"
        path = THREE_STAR_PATH
    else:
        star = "2star"
        path = TWO_STAR_PATH

    cards = list(path.glob("*.*"))
    if not cards:
        raise FileNotFoundError(f"卡牌图片缺失：{path}")
    return random.choice(cards), star


async def generate_result_image(card_paths: List[Tuple[Path, str]], is_multi: bool) -> Path:
    try:
        bg_image = Image.open(random.choice(list(BG_PATH.glob("*.*")))).resize(BG_SIZE)

        if is_multi:
            for idx, (card_path, _) in enumerate(card_paths):
                card = Image.open(card_path).resize(CARD_SIZE_MULTI)
                bg_image.paste(card, GRID_LAYOUT[idx])
        else:
            card = Image.open(card_paths[0][0]).resize(CARD_SIZE_SINGLE)
            x = (BG_SIZE[0] - CARD_SIZE_SINGLE[0]) // 2
            y = (BG_SIZE[1] - CARD_SIZE_SINGLE[1]) // 2
            bg_image.paste(card, (x, y))

        output_path = TEMP_PATH / f"{datetime.now().timestamp()}.png"
        bg_image.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"图片合成失败: {str(e)}") from e


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


@gacha_handler.handle()
async def handle_gacha(event: GroupMessageEvent):
    try:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        command = event.get_plaintext()

        if command == "pjsk单抽":
            card_path, star = await get_random_card()
            image_path = await generate_result_image([(card_path, star)], False)
            msg = await build_message(event, image_path, [(card_path, star)])
        elif command == "pjsk十连":
            results = []
            has_high_star = False

            for _ in range(9):
                card, star = await get_random_card()
                results.append((card, star))
                if star in ("3star", "4star"):
                    has_high_star = True

            if not has_high_star:
                total_high_prob = PROBABILITY["3star"] + PROBABILITY["4star"]
                rand = random.uniform(0, total_high_prob)
                star = "4star" if rand < PROBABILITY["4star"] else "3star"
                path = FOUR_STAR_PATH if star == "4star" else THREE_STAR_PATH
                cards = list(path.glob("*.*"))
                if not cards:
                    raise FileNotFoundError(f"找不到{star}卡牌图片")
                results.append((random.choice(cards), star))
            else:
                results.append(await get_random_card())

            image_path = await generate_result_image(results, True)
            msg = await build_message(event, image_path, results)
        else:
            return

        await gacha_handler.finish(msg)

    except FinishedException:
        pass

    except Exception as e:
        logger.exception("抽卡处理失败")
        try:
            await gacha_handler.finish(f"抽卡失败：{str(e)}")
        except FinishedException:
            pass