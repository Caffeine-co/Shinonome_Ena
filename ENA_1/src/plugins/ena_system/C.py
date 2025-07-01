# --------------------------
# 导入区域
# --------------------------
import json
import random
from pathlib import Path
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.rule import startswith

from ._430_ import check_group_whitelist, check_user_blacklist, check_blindgoods_usage



# --------------------------
# 配置区域
# --------------------------
# 加载配置文件
# current_dir = Path(__file__).parent
# config_path = current_dir / "blindbox_config.json"

# config_path = Path("C:/QQbot/ENANA/src/plugins/blindgoods/blindbox_config.json")
config_path = Path(__file__).parent / "resources/C/blindbox_config.json"



# --------------------------
# 文件操作
# --------------------------
# 读取JSON配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)



# --------------------------
# 事件响应器
# --------------------------
# 创建消息响应器，严格匹配"抽"开头的指令
draw_handler = on_message(rule=startswith("抽一发"), block=False)



# --------------------------
# 事件处理
# --------------------------
@draw_handler.handle()
async def handle_draw(event: GroupMessageEvent):
    # 获取用户id
    user_id = event.get_user_id()

    # 白名单验证
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单验证（紧接白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await draw_handler.finish(Message([
        #       MessageSegment.reply(event.message_id),
        #       MessageSegment.text("您已被禁用Ena-bot")
        #   ]))
        return

    # 提取指令内容
    command = event.get_plaintext()  # .strip()
    if not command.startswith("抽一发"):
        return

    # 获取款式名称
    style = command[3:]  # .strip()
    if not style or style not in config:
        await draw_handler.finish(
            MessageSegment.reply(event.message_id) + "Ena没有收录这个款式捏"
        )
        # return

    # 检查使用限制
    if not (await check_blindgoods_usage(user_id)):
        await draw_handler.finish(
            MessageSegment.reply(event.message_id) + "今天抽了很多了，明天再来吧"
        )

    # 获取配置信息
    style_config = config[style]
    max_num = style_config["max"]

    # 生成随机数
    random_num = random.randint(1, max_num)

    # 查找对应角色
    character = None
    for key in sorted(map(int, style_config["characters"].keys())):
        if random_num <= key:
            character = style_config["characters"][str(key)]
            break

    if not character:
        return

    # try:
    # 构建消息
    message = Message()
    message += MessageSegment.reply(event.message_id)
    message += MessageSegment.text(f"恭喜抽中[{character['name']}]哒~\n")
    message += MessageSegment.image(file=character["image"])

    await draw_handler.send(message)
    # except Exception as e:
    #    await draw_handler.send(f"消息发送失败: {str(e)}")