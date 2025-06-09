import aiofiles
import json
import os
import random
from pathlib import Path
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, MessageSegment

WHITELIST_PATH = Path(__file__).parent / "group_whitelist.json"
BLACKLIST_PATH = Path(__file__).parent / "user_blacklist.json"

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

        random_num = random.randint(1, 8)

        if random_num == 1:
            message = MessageSegment.text("Akito!")
        elif random_num == 2:
            message = MessageSegment.text("还我松饼！")
        elif random_num == 3:
            message = MessageSegment.text("还我芝士蛋糕！")
        elif random_num == 4:
            message = MessageSegment.text("哎，不想上学")
        else:
            image_dir = "C:/QQbot/ENANA/src/plugins/image/"

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

        await poke_notice.send(message)