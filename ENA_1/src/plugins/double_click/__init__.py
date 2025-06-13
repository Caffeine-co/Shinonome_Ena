import aiofiles
import json
import os
import random
from pathlib import Path
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, MessageSegment

WHITELIST_PATH = Path("***/ENA_1/src/plugins/group_whitelist.json")
BLACKLIST_PATH = Path("***/ENA_1/src/plugins/user_blacklist.json")


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
    except Exception:
        return True

poke_notice = on_notice()


@poke_notice.handle()
async def handle_poke(event: PokeNotifyEvent):
    if event.sub_type == "poke" and event.target_id == event.self_id and event.group_id:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        random_num = random.randint(1, 3)

        if random_num == 1:

            option1 = "Akito!"
            option2 = "还我松饼！"
            option3 = "还我芝士蛋糕！"
            option4 = "哎，不想上学"

            result = random.choice([option1, option2, option3, option4])

            message = MessageSegment.text(f"{result}")

        elif random_num == 2:
            image_dir = Path(__file__).parent / "image/"

            try:
                image_files = [
                    f for f in os.listdir(image_dir)
                    if os.path.isfile(os.path.join(image_dir, f))
                       and f.lower().endswith('.gif')
                ]

                if image_files:
                    selected_image = random.choice(image_files)
                    image_path = os.path.join(image_dir, selected_image)
                    message = MessageSegment.image(file=image_path)
                else:
                    message = MessageSegment.text("图片不见啦～")
            except FileNotFoundError:
                message = MessageSegment.text("找不到图片目录哦")

        else:
            voice_dir = Path(__file__).parent / "voice/"

            try:
                voice_files = [
                    f for f in os.listdir(voice_dir)
                    if os.path.isfile(os.path.join(voice_dir, f))
                       and f.lower().endswith('wav')
                ]

                if voice_files:
                    selected_voice = random.choice(voice_files)
                    voice_path = os.path.join(voice_dir, selected_voice)
                    message = MessageSegment.record(file=voice_path)
                else:
                    message = MessageSegment.text("文件不存在")
            except FileNotFoundError:
                message = MessageSegment.text("找不到文件目录")

        await poke_notice.finish(message)