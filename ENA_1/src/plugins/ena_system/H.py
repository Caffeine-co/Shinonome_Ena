# --------------------------
# 导入区域
# --------------------------
import os  # 新增os模块用于文件操作
import random
from pathlib import Path  # 新增Path模块
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, MessageSegment

from  ._430_ import check_group_whitelist, check_user_blacklist



# --------------------------
# 事件响应器
# --------------------------
poke_notice = on_notice()



# --------------------------
# 事件处理
# --------------------------
@poke_notice.handle()
async def handle_poke(event: PokeNotifyEvent):
    # 判断是否为双击头像的戳一戳事件，并且发生在群聊中
    if event.sub_type == "poke" and event.target_id == event.self_id and event.group_id:
        # 新增白名单检查
        if not await check_group_whitelist(event.group_id):
            #   await poke_notice.finish("❌ 该群未授权使用此功能")
            return

        # 黑名单验证（紧接白名单之后）
        if await check_user_blacklist(event.user_id):
            #   await poke_notice.finish(
                #   MessageSegment.reply(event.message_id) + MessageSegment.text("⛔ 您无权限使用此功能")
            return

        # 生成1-3的随机数决定响应类型
        random_num = random.randint(1, 3)

        if random_num == 1:
            # 文字回复

            option1 = "Akito!"   # 第一种文字回复
            option2 = "还我松饼！"   # 第二种文字回复
            option3 = "还我芝士蛋糕！"   # 第三种文字回复
            option4 = "哎，不想上学"   # 第四种文字回复

            # 随机选择结果
            result = random.choice([option1, option2, option3, option4])

            message = MessageSegment.text(f"{result}")

        elif random_num == 2:
            # 图片文件目录路径（根据实际情况修改）
            image_dir = Path(__file__).parent / "resources/H/image/"

            try:
                # 获取目录下所有图片文件（支持jpg/png/gif格式）
                #image_files = [
                #    f for f in os.listdir(image_dir)
                #    if os.path.isfile(os.path.join(image_dir, f))  # 确保是文件
                #       and f.lower().endswith(('.jpg', '.png', '.gif'))  # 检查扩展名
                #]

                # 获取目录下所有GIF图片文件
                image_files = [
                    f for f in os.listdir(image_dir)
                    if os.path.isfile(os.path.join(image_dir, f))  # 确保是文件
                       and f.lower().endswith('.gif')  # 仅检查gif扩展名
                ]

                if image_files:
                    # 从图片列表中随机选择一个
                    selected_image = random.choice(image_files)
                    # 拼接完整文件路径
                    image_path = os.path.join(image_dir, selected_image)
                    # 构建图片消息
                    message = MessageSegment.image(file=image_path)
                else:
                    # 目录为空时的备用回复
                    message = MessageSegment.text("图片不见啦～")
            except FileNotFoundError:
                # 目录不存在时的错误处理
                message = MessageSegment.text("找不到图片目录哦")

        else:
            # 音频文件目录路径（根据实际情况修改）
            voice_dir = Path(__file__).parent / "resources/H/voice/"

            try:
                # 获取目录下所有wav文件
                voice_files = [
                    f for f in os.listdir(voice_dir)
                    if os.path.isfile(os.path.join(voice_dir, f))  # 确保是文件
                       and f.lower().endswith('wav')  # 检查扩展名
                ]

                if voice_files:
                    # 从wav列表中随机选择一个
                    selected_voice = random.choice(voice_files)
                    # 拼接完整文件路径
                    voice_path = os.path.join(voice_dir, selected_voice)
                    # 构建语音消息
                    message = MessageSegment.record(file=voice_path)
                else:
                    # 目录为空时的备用回复
                    message = MessageSegment.text("文件不存在")
            except FileNotFoundError:
                # 目录不存在时的错误处理
                message = MessageSegment.text("找不到文件目录")

        # 发送生成的消息
        await poke_notice.finish(message)