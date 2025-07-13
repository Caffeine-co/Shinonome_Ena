# --------------------------
# 导入区域
# --------------------------
import os  # 新增os模块用于文件操作
import random
from pathlib import Path  # 新增Path模块
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent, MessageSegment
from nonebot.matcher import Matcher

from  ._430_ import check_group_whitelist, check_user_blacklist


# --------------------------
# 事件响应器
# --------------------------
double_click = on_notice()


# --------------------------
# 事件处理
# --------------------------
@double_click.handle()
async def double_click_handler(bot: Bot, event: PokeNotifyEvent):
    if event.target_id == event.self_id:
        if not await check_group_whitelist(event.group_id):
            return

        if await check_user_blacklist(event.user_id):
            return

        random_num = random.randint(1, 4)

        if random_num == 1:

            option1 = "Akito!"
            option2 = "还我松饼！"
            option3 = "还我芝士蛋糕！"
            option4 = "哎，不想上学"

            result = random.choice([option1, option2, option3, option4])

            message = MessageSegment.text(f"{result}")

            await double_click.finish(message)

        elif random_num == 2:
            image_dir = Path(__file__).parent / "resources/H/image/"

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

            await double_click.finish(message)

        elif random_num == 3:
            voice_dir = Path(__file__).parent / "resources/H/voice/"

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

            await double_click.finish(message)

        else:
            await bot.group_poke(group_id=event.group_id, user_id=event.user_id)