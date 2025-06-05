import os
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

ena_help = on_fullmatch(("help","帮助"))
ena_pjsk_help = on_fullmatch(("pjskhelp","pjsk帮助"))
ena_bottle_help = on_fullmatch("漂流瓶帮助")
ena_guesscard_help = on_fullmatch("猜卡面帮助")
ena_blindgoods_help = on_fullmatch(("周边盲抽帮助","谷子盲抽帮助"))
ena_calculator_help = on_fullmatch(("计算帮助","计算器帮助"))
ena_aichat_help = on_fullmatch(("聊天帮助","ai聊天帮助","AI聊天帮助"))
ena_gacha_help = on_fullmatch(("抽卡帮助","模拟抽卡帮助"))

@ena_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text1 = "\
🎨Shinonome Ena使用帮助🎨"
    image = MessageSegment.image(os.path.join(os.path.dirname(__file__), 'enahelp.jpg'))
    text2 = "\
小窝：絵名の部屋[728556872]\n\
主人：咖啡不甜[2083909754]\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text1 + image + text2
        }
    })

    text = "\
🎨ENA功能一览🎨\n\n\
HarukiBot使用帮助\n\
⭕[pjskhelp/pjsk帮助]\n\n\
抽签\n\
⭕[抽签/求签+空格+事件]\n\n\
每日问候\n\
⭕[早上好/中午好/下午好/晚上好/晚安]\n\
    暂停使用\n\n\
群聊复读\n\
⭕[无触发指令]\n\
    暂停使用\n\n\
漂流瓶\n\
⭕发送“漂流瓶帮助”查看详细使用方法\n\n\
属性鉴定\n\
⭕[鉴定]\n\n\
ai聊天\n\
⭕发送“ai聊天帮助”查看详细使用方法\n\n\
二选一\n\
⭕[@我 a还是b]\n\n\
猜卡面\n\
⭕发送“猜卡面帮助”查看详细使用方法\n\n\
pjsk模拟招募\n\
⭕发送“抽卡帮助”查看详细使用方法\n\n\
pjsk模拟计算器\n\
⭕发送“计算器帮助”查看详细使用方法\n\n\
赛博周边盲抽\n\
⭕发送“周边盲抽帮助/谷子盲抽帮助”查看详细使用方法\n\n\
运行状态查看\n\
⭕[status/状态]\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
===== bot人设原型 =====\n\
Shinonome Ena 东云绘名\n\
东云绘名（東雲 絵名，しののめ えな）是《世界计划 彩色舞台 feat. 初音未来》（Project SEKAI, PJSK）及其衍生作品的登场角色。代表色为 #ccaa88。\n\
"
    image = MessageSegment.image(os.path.join(os.path.dirname(__file__), 'ena.jpg'))

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text + image
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_pjsk_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的HarukiBot使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨以下功能由Ena②[絵名の絵名]负责发送\n\
感谢星雲希凪及其团队提供的HarukiBot服务,更多指令细则请阅读HarukiBot帮助文档：\n\n\
https://docs.haruki.seiunx.com\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨pjsk歌曲信息相关查询\n\n\
⭕[pjskinfo/song/musicinfo+曲名]\n\
⭕[pjskbpm+曲名]\n\
⭕[查bpm+数字]\n\
⭕[谱面预览+曲名(+难度)]\n\
    ⭐难度支持的输入: easy, normal, hard, expert, master, append, ez, nm, hd, ex, ma, ap, apd\n\
⭕[charalias+昵称]\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨玩家信息相关查询\n\n\
    ⭐在命令前加cn/en/tw/kr即可查询国服/国际服/台服/韩服信息，如cn绑定, twsk, kr逮捕, enpjskprofile\n\n\
⭕[绑定+id]\n\
⭕[sk]\n\
⭕[sk+游戏数字id]\n\
⭕[sk+排名]\n\
⭕[查房/cf+排名]\n\
⭕[sk线]\n\
⭕[时速]\n\
⭕[半日速]\n\
⭕[日速]\n\
⭕[分数线/rtr+排名]\n\
⭕[追踪/ptr]\n\
⭕[追踪/ptr+排名]\n\
⭕[逮捕]\n\
⭕[逮捕@xxx]\n\
⭕[逮捕+id]\n\
⭕[pjskprofile/个人信息]\n\
⭕[不给看]\n\
⭕[给看]\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨MySekai相关查询\n\n\
    ⭐在使用该功能前请确保已上传MySekai数据至Haruki数据库，如未上传请按照帮助文档中对应模块进行上传\n\n\
⭕[mysekai_analyze/mysekai分析/ms分析/msa]\n\
⭕[mysekai_analyze2/mysekai分析2/ms分析2/msa2]\n\
⭕[mysekai_maps/msm/mysekai地图/ms地图]\n\
⭕[mysekai照片/ms照片/msp+序号]\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨卡牌及活动信息相关查询\n\n\
⭕[查卡/查卡面/查询卡面/findcard+角色昵称]\n\
⭕[查卡/查卡面/查询卡面/cardinfo+卡面id]\n\
⭕[card+卡面id]\n\
⭕[查活动/查询活动/event+活动id]\n\
⭕[查活动/查询活动/findevent+关键字]\n\
⭕[活动图鉴/活动列表/活动总览/findevent all]\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_bottle_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的漂流瓶使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[捡漂流瓶]\n\
    由Ena为你从空无一人的世界的湖里捞起一个寄托了他人心愿的漂流瓶\n\n\
⭕[扔漂流瓶]\n\
    可以将自身心愿寄托在漂流瓶中并交给Ena扔进湖里\n\n\
⭕[查看漂流瓶]\n\
    委托Ena帮你从湖里捞起所有你扔过的漂流瓶\n\n\
⭕[查看漂流瓶+编号]\n\
    委托Ena帮你从湖里捞起你扔过的指定编号的漂流瓶\n\n\
⭕[删除漂流瓶+编号]\n\
    让Ena帮你销毁指定编号的漂流瓶\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 漂流瓶内容仅支持文字、符号和emoji\n\
• 每人每天仅有一次机会扔瓶子，退出也记作一次\n\
• 查看、删除漂流瓶仅支持漂流瓶持有者本人\n\
• 删除漂流瓶请谨慎操作，数据删除后无法恢复\n\
• 请勿输入过长文本，否则“查看漂流瓶”无法发出\n\
• 请勿在漂流瓶中输入不宜内容，提醒后毫无悔改者做全局拉黑处理\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_guesscard_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的猜卡面使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[猜卡面]\n\
    由Ena从游戏中已有的三、四星卡的花前、花后中随机挑选一张并裁剪至200*200像素大小并开始一次猜卡面游戏\n\n\
    ⭕[引用区域图片消息+角色名称]\n\
        回答当前的猜卡面游戏\n\n\
    ⭕[引用区域图片消息+结束猜卡面]\n\
        退出当前的猜卡面游戏\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 每人每天仅有十次猜卡面机会，结束猜卡面也记作一次\n\
• 单次猜卡面回答时间约为30秒\n\
• 回答时请务必引用原区域图片消息\n\
• 支持角色花名核对，所采用花名为Haruki数据库所收录角色花名，更新日期：2025.2.27\n\
• 游戏全流程仅支持本人进行作答\n\
• 由于附带图片导致消息较长，请自行处理刷屏问题\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_blindgoods_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的周边盲抽使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[抽一发+周边名称]\n\
    由Ena为你从指定名称的周边中抽取一枚周边，角色款式随机\n\
    可供选择的名称列表如下：\n\
    ⭐神高吧唧\n\
    ⭐神高透卡\n\
    ⭐神高星挂\n\
    ⭐神高色纸\n\
    ⭐神高立牌\n\
    ⭐感谢祭吧唧\n\
    ⭐感谢祭心砖\n\
    ⭐感谢祭挂件\n\
    ⭐感谢祭ep\n\
    ⭐宝石箱镜子画\n\
    ⭐三丽鸥豆豆眼\n\
    ⭐新队服吧唧\n\
    （感谢祭系列为四周年感谢祭）\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 每人每天有五次机会抽取周边，不要抽多哦\n\
• 不支持未收录的周边款式\n\
• 由于附带图片导致消息较长，请自行处理刷屏问题\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_calculator_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的模拟计算器使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[计算倍率/倍率计算 a b c d e]\n\
    输入游戏中的五张卡的技能分数加成进行模拟倍率计算\n\
    例：计算倍率 150 150 150 150 150\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[协力pt/计算pt a b c d]\n\
    输入拟定的协力live参数进行模拟pt计算\n\
    a：个人live分数\n\
    b：歌曲加成\n\
    c：卡组加成\n\
    d：体力消耗加成\n\
    默认队友live平均分数为110w\n\
    例：协力pt 3000000 1 500 25\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[单人pt a b c d]\n\
    输入拟定的单人live参数进行模拟pt计算\n\
    a：个人live分数\n\
    b：歌曲加成\n\
    c：卡组加成\n\
    d：体力消耗加成\n\
    例：单人pt 3000000 1 500 25\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[挑战pt a]\n\
    输入拟定的协力live参数进行模拟pt计算\n\
    a：挑战live分数\n\
    例：挑战pt 3000000\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 倍率计算、pt计算均为模拟计算，存在公式系统误差，\n\
• 模拟pt计算公式来自于b站xfl03的相关专栏\n\
• 计算结果仅作参考，如需精确计算倍率、pt等数据请自行寻找工具\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_aichat_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的ai聊天使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕以指定称呼为开头进行触发\n\
    称呼列表：“ena”、“enana”、“绘名”、“东云绘名”、“饿娜娜”、“恶娜娜”\n\
    例：ena，你该起床了\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 若要使用ai聊天请携带群聊联系bot主进行评估\n\
• 该玩法需调用deepseek的API，需要进行收费，故聊天请勿上头\n\
• 由于deepseek官方的API未提供联网，实际聊天会出现部分信息与现实生活不符，属正常情况\n\
• 使用时请勿输入不宜内容或敏感信息，提醒后毫无悔改者做全局拉黑处理\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )



@ena_gacha_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的模拟游戏招募使用帮助🎨\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
⭕[pjsk单抽]\n\
    由Ena为你从给定普通卡池中招募一位成员\n\n\
⭕[pjsk十连]\n\
    由Ena为你从给定普通卡池中招募十位成员\n\n\
⭕[pjsk限定单抽]\n\
    由Ena为你从给定限定卡池中招募一位成员\n\n\
⭕[pjsk限定十连]\n\
    由Ena为你从给定限定卡池中招募十位成员\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
🎨注意事项🎨\n\
• 每人每天有50抽的总抽数，不要抽多哦\n\
• 限定招募中包含有普通限定，fes限定，大罪、三丽鸥、es联动限定、剧场版限定\n\
• 由于附带图片导致消息较长，请自行处理刷屏问题\n\
"

    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    if isinstance(ev, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=ev.group_id,
            messages=msg
        )