# --------------------------
# 导入区域
# --------------------------
import aiofiles
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment, MessageEvent
from nonebot.params import EventPlainText, RegexGroup

from  ._430_ import check_group_whitelist, check_user_blacklist, check_bottles_usage



# --------------------------
# 配置区域
# --------------------------
# ========== 权限配置 ==========
ADMIN_GROUP_ID = 1017564050
ADMIN_QQ = 2083909754
BOTTLE_FILE = Path(__file__).parent / "resources/D/bottles.json"



# --------------------------
# 事件响应器
# --------------------------
throw_bottle = on_fullmatch("扔漂流瓶")
pick_bottle = on_fullmatch("捡漂流瓶")
#   cancel_throw = on_fullmatch("退出")
delete_bottle = on_regex(r"^删除漂流瓶(\d+)$")
view_bottle = on_regex(r"^查看漂流瓶(\d*)$")



# --------------------------
# 文件操作
# --------------------------
async def read_bottles() -> List[Optional[Dict]]:
    """异步读取漂流瓶数据"""
    if not os.path.exists(BOTTLE_FILE):
        return []
    try:
        async with aiofiles.open(BOTTLE_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content) if content else []
    except:
        return []


async def write_bottles(bottles: List[Optional[Dict]]):
    """异步写入漂流瓶数据"""
    async with aiofiles.open(BOTTLE_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(bottles, ensure_ascii=False, indent=2))


async def save_bottle(data: Dict) -> Tuple[int, bool]:
    """保存漂流瓶并返回（编号，是否新建）"""
    bottles = await read_bottles()
    # 寻找第一个空位（编号对应索引+1）
    for index, item in enumerate(bottles):
        if item is None:
            data["bottle_id"] = index + 1  # 固定编号
            bottles[index] = data
            await write_bottles(bottles)
            return index + 1, False
    # 没有空位则追加
    data["bottle_id"] = len(bottles) + 1  # 新编号为当前长度+1
    bottles.append(data)
    await write_bottles(bottles)
    return len(bottles), True  # 返回新编号



# --------------------------
# 事件处理
# --------------------------
@throw_bottle.handle()
async def throw_start(event: GroupMessageEvent):
    """扔漂流瓶初始化"""
    """双重权限检查"""
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单检查（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await throw_bottle.finish(
        #      MessageSegment.reply(event.message_id) + "您已被禁用Ena-bot"
        #   )
        return

    # 检查使用限制
    user_id = event.get_user_id()
    if not (await check_bottles_usage(user_id)):
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "今天已经扔过瓶子了，明天再来吧"
        )

    await throw_bottle.send(
        MessageSegment.reply(event.message_id) + "• 输入文本写进漂流瓶\n• 输入“退出”取消扔漂流瓶\n• 请勿在漂流瓶中输入违规或不宜内容，一经发现立刻拉黑"
    )


@throw_bottle.got("content")
async def throw_get_content(
        bot: Bot,
        event: GroupMessageEvent,
        content: str = EventPlainText()
):
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单检查（紧随白名单之后）
    if await check_user_blacklist(event.user_id):
        #   await throw_bottle.finish(
        #      MessageSegment.reply(event.message_id) + "您已被禁用Ena-bot"
        #   )
        return

    """处理漂流瓶内容"""
    if content.strip() == "退出":
        await throw_bottle.finish(
            MessageSegment.reply(event.message_id) + "已取消扔漂流瓶"
        )

    # 获取群信息
    try:
        group_info = await bot.get_group_info(group_id=event.group_id)
        group_name = group_info["group_name"]
    #   except:
    #   group_name = "未知群组"
    except Exception as e:
        group_name = f"未知群聊（{str(e)}）"

    # 构建数据（包含固定编号）
    bottle_data = {
        "user_id": event.user_id,
        "nickname": event.sender.card or event.sender.nickname,
        "group_id": event.group_id,
        "group_name": group_name,
        "content": content.strip(),
        "timestamp": int(time.time())
    }

    # 保存数据
    bottle_id, is_new = await save_bottle(bottle_data)

    # 发送到管理群
    admin_msg = (
        f"新的漂流瓶:No.{bottle_id}\n"
        f"来自：{bottle_data['nickname']}({event.user_id})\n"
        f"群聊：{group_name}({event.group_id})\n"
        f"内容：{content.strip()}"
    )
    await bot.send_group_msg(group_id=ADMIN_GROUP_ID, message=admin_msg)

    # 回复用户
    reply = f"漂流瓶No.{bottle_id}已扔进空无一人的湖中"  # + ("（填补了空缺位置）" if not is_new else "")
    await throw_bottle.finish(MessageSegment.reply(event.message_id) + reply)


# ========== 退出流程 ==========
#   @cancel_throw.handle()
#   async def cancel_process(event: GroupMessageEvent):
#   """取消操作处理"""
#   await cancel_throw.finish(
#   MessageSegment.reply(event.message_id) + "已退出当前流程"
#   )


# ========== 捡漂流瓶 ==========
@pick_bottle.handle()
async def pick_process(bot: Bot, event: GroupMessageEvent):
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单检查
    if await check_user_blacklist(event.user_id):
        #   await pick_bottle.finish(
        #       MessageSegment.reply(event.message_id) + "您已被禁用Ena-bot"
        #   )
        return

    bottles = await read_bottles()
    valid_bottles = [b for b in bottles if b is not None]

    if not valid_bottles:
        await pick_bottle.finish(
            MessageSegment.reply(event.message_id) + "暂时没有漂流瓶哦～"
        )

    bottle = random.choice(valid_bottles)

    msg = []

    text = MessageSegment.text("Ena为你捡到了一个漂流瓶")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"编号：No.{bottle['bottle_id']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"来自：{bottle['nickname']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text(f"内容：\n{bottle['content']}")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=event.group_id,
            messages=msg
        )

    # msg = (
    #    f"漂流瓶No.{bottle['bottle_id']}\n"
    #    f"来自：{bottle['nickname']}\n"
    #    f"内容：{bottle['content']}"
    # )

    # await pick_bottle.finish(MessageSegment.reply(event.message_id) + msg)


# ========== 删除漂流瓶 ==========
@delete_bottle.handle()
async def delete_process(
        bot: Bot,
        event: GroupMessageEvent,
        reg: Tuple[str, ...] = RegexGroup()
):
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        #   await draw_handler.finish("本群未授权")
        return

    # 黑名单检查
    if await check_user_blacklist(event.user_id):
        #   await pick_bottle.finish(
        #       MessageSegment.reply(event.message_id) + "您已被禁用Ena-bot"
        #   )
        return

    try:
        bottle_id = int(reg[0])
        # 转换为数组索引（编号-1）
        index = bottle_id - 1
    except ValueError:
        await delete_bottle.finish("无效的编号格式", reply_message=True)

    bottles = await read_bottles()
    if index < 0 or index >= len(bottles) or bottles[index] is None:
        await delete_bottle.finish(f"你要删除的漂流瓶No.{bottle_id}不存在哦～", reply_message=True)

    bottle = bottles[index]
    current_user_id = event.user_id
    bottle_owner_id = bottle["user_id"]

    # 权限检查：管理员或漂流瓶主人
    if current_user_id != ADMIN_QQ and current_user_id != bottle_owner_id:
        await delete_bottle.finish(
            MessageSegment.reply(event.message_id) + "Ena认为你没有权限删除这个漂流瓶哦～"
        )

    # 管理员也需要黑名单检查
    #   if await check_user_blacklist(event.user_id):
    #   await delete_bottle.finish(
    #       MessageSegment.reply(event.message_id) + "账号状态异常，操作终止"
    #   )
    #   return

    # 执行删除操作并标记删除（保留位置）
    bottles[index] = None
    await write_bottles(bottles)

    await delete_bottle.finish(
        MessageSegment.reply(event.message_id) + f"Ena已帮你删除漂流瓶No.{bottle_id}"
    )


# ========== 查看漂流瓶 ==========
@view_bottle.handle()
async def view_bottle_process(bot: Bot, event: MessageEvent, reg: Tuple[str, ...] = RegexGroup()):
    """处理查看漂流瓶请求"""
    # 白名单检查
    if not await check_group_whitelist(event.group_id):
        return
    # 黑名单检查
    if await check_user_blacklist(event.user_id):
        return


    # 获取请求参数
    bottle_id_str = reg[0]
    user_id = event.user_id

    # 读取漂流瓶数据
    bottles = await read_bottles()
    user_bottles = []
    for idx, bottle in enumerate(bottles):
        if bottle and str(bottle["user_id"]) == str(user_id):
            user_bottles.append((idx + 1, bottle))  # 存储（编号，数据）

    # 无漂流瓶的情况
    if not user_bottles:
        await view_bottle.finish("你还没有扔过任何漂流瓶哦～", reply_message=True)

    # 查看特定漂流瓶
    if bottle_id_str:
        try:
            #target_id = int(bottle_id_str)
            # 查找指定编号且属于用户的瓶子
            #target_bottle = next((b for num, b in user_bottles if num == target_id), None)
            #if not target_bottle:
            #    await view_bottle.finish(f"未找到你扔出的No.{target_id}漂流瓶", reply_message=True)

            target_id = int(bottle_id_str)
            # 先检查瓶子是否存在（全局查找）
            target_bottle = None
            for idx, bottle in enumerate(bottles):
                if bottle and (idx + 1) == target_id:  # 编号对应索引+1
                    target_bottle = bottle  # 正确赋值给 target_bottle
                    break

            if not target_bottle:
                await view_bottle.finish(f"Ena没有找到你扔过的No.{target_id}漂流瓶呢", reply_message=True)

            # 再检查所属权
            if str(target_bottle["user_id"]) != str(user_id):
                await view_bottle.finish(
                    MessageSegment.reply(event.message_id) +
                    f"漂流瓶No.{target_id}不属于你哦"
                )

            # 格式化时间
            dt = datetime.fromtimestamp(target_bottle["timestamp"])
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            # 构建消息
            msg = []

            text = MessageSegment.text(f"昵称：{target_bottle['nickname']}\nQQ：{target_bottle['user_id']}\n昵称为扔漂流瓶时记录的群内昵称")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶编号：No.{target_id}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶扔出时间：{time_str}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            text = MessageSegment.text(f"漂流瓶内容：\n{target_bottle['content']}")
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

            if isinstance(event, GroupMessageEvent):
                await bot.send_group_forward_msg(
                    group_id=event.group_id,
                    messages=msg
                )
                #await view_bottle.finish()
            #else:
                #await view_bottle.finish("此功能仅限群聊使用")

        except ValueError:
            await view_bottle.finish("请输入有效的漂流瓶编号", reply_message=True)


    # 列出所有漂流瓶编号
    # 修改无编号时的列表展示逻辑
    else:
        # 按时间排序
        sorted_bottles = sorted(user_bottles, key=lambda x: x[1]["timestamp"], reverse=True)

        # 获取当前用户信息
        user_id = event.user_id
        nickname = event.sender.card or event.sender.nickname  # 优先群名片

        # 构建转发消息
        msg = []

        # 用户信息节点
        user_info = f"昵称：{nickname}\nQQ：{user_id}"

        msg.append({
            "type": "node",
            "data": {
                "name": "Shinonome Ena",
                "uin": bot.self_id,
                "content": MessageSegment.text(user_info)
            }
        })

        # 引导节点
        total_count = len(sorted_bottles)
        display_count = min(100, total_count)
        header = f"Ena为你捞起了你扔过的所有漂流瓶，共{total_count}个"
        if total_count > 100:
            header += f"，显示最近{display_count}个"

        msg.append({
            "type": "node",
            "data": {
                "name": "Shinonome Ena",
                "uin": bot.self_id,
                "content": MessageSegment.text(header)
            }
        })

        # 内容节点（分页逻辑）
        content_lines = []
        for num, bottle in sorted_bottles[:100]:
            dt = datetime.fromtimestamp(bottle["timestamp"])
            time_str = dt.strftime("%m-%d %H:%M")
            line = f"🆔 No.{num} | 🕒 {time_str} | 👥 {bottle['group_name']}"
            content_lines.append(line)

        # 添加提示信息
        if total_count > 100:
            content_lines.append(f"\n查看完整列表请使用具体编号查询")

        # 分节点发送（每10条一个节点）
        chunk_size = 10
        for i in range(0, len(content_lines), chunk_size):
            chunk = content_lines[i:i + chunk_size]
            text = MessageSegment.text("\n".join(chunk))
            msg.append({
                "type": "node",
                "data": {
                    "name": "Shinonome Ena",
                    "uin": bot.self_id,
                    "content": text
                }
            })

        # 发送转发消息
        if isinstance(event, GroupMessageEvent):
            await bot.send_group_forward_msg(
                group_id=event.group_id,
                messages=msg
            )


# ========== 群聊校验 ==========
#   @throw_bottle.handle()
#   @pick_bottle.handle()
#   @cancel_throw.handle()
#   @delete_bottle.handle()
#   async def group_check(event: MessageEvent):
#   """全局群聊校验"""
#   if not isinstance(event, GroupMessageEvent):
#   await throw_bottle.finish("请在群聊中使用漂流瓶功能～")
#   pass