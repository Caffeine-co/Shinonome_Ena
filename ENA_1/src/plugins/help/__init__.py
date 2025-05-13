import os
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

ena_help = on_fullmatch(("help","帮助"))
ena_pjsk_help = on_fullmatch(("pjskhelp","pjsk帮助"))
ena_bottle_help = on_fullmatch("漂流瓶帮助")
ena_guesscard_help = on_fullmatch("猜卡面帮助")
ena_blindgoods_help = on_fullmatch(("周边盲抽帮助","谷子盲抽帮助"))

@ena_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text1 = "\
🎨Shinonome Ena使用帮助🎨"
    image = MessageSegment.image(os.path.join(os.path.dirname(__file__), 'enahelp.jpg'))
    text2 = "\
小窝：絵名の部屋[728556872]\n\
主人：咖啡不甜[2083909754]"
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
⭕[pjskhelp/pjsk帮助]\n\
    该功能由Ena②[絵名の絵名]负责发送\n\n\
抽签\n\
⭕[抽签/求签+空格+事件]\n\n\
每日问候\n\
⭕[早上好/中午好/下午好/晚上好/晚安]\n\
    暂停使用\n\n\
群聊复读\n\
⭕[无触发指令]\n\
    暂停使用\n\n\
漂流瓶\n\
⭕[捡/扔漂流瓶]\n\
    发送“漂流瓶帮助”查看详细使用方法\n\n\
二选一\n\
⭕[@我 a还是b]\n\n\
猜卡面\n\
⭕[猜卡面]\n\
    发送“猜卡面帮助”查看详细使用方法\n\n\
    注意事项：\n\
        • 支持角色别称识别，所采用别称为Haruki数据库所收录角色别称，更新日期：2025.2.27\n\
        • 游戏全流程仅支持本人进行作答\n\n\
pjsk模拟招募\n\
⭕[pjsk(限定)单抽/十连]\n\
    限定招募中包含有普通限定，fes限定，大罪、三丽鸥、es联动限定、剧场版限定\n\n\
倍率计算器\n\
⭕[计算倍率 a b c d e]\n\n\
赛博周边盲抽\n\
⭕[抽一发+周边名称]\n\
    发送“周边盲抽帮助/谷子盲抽帮助”查看详细使用方法\n\n\
属性鉴定\n\
⭕[鉴定]\n\n\
ai语c\n\
⭕[ena/绘名+对话内容]\n\
    仅限主群使用\n\n\
运行状态查看\n\
⭕[status/状态]\n"
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text("\
===== bot人设原型 =====\n\
Shinonome Ena 东云绘名\n\
东云绘名（東雲 絵名，しののめ えな）是《世界计划 彩色舞台 feat. 初音未来》（Project SEKAI, PJSK）及其衍生作品的登场角色。代表色为 #ccaa88。")
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

    text = ("\
🎨Shinonome Ena使用帮助🎨\n\
小窝：絵名の部屋[728556872]\n\
主人：咖啡不甜[2083909754]")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
以下功能感谢星雲希凪及其团队提供的HarukiBot服务,更多指令细则请阅读HarukiBot帮助文档[https://docs.haruki.seiunx.com]\n\n\
功能一览请发送[help]查看"
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = ("\
pjsk歌曲信息相关查询\n\n\
⭕[pjskinfo/song/musicinfo+曲名]\n\
    查看当前歌曲详细信息\n\
⭕[pjskbpm+曲名]\n\
    查看当前歌曲的bpm\n\
⭕[查bpm+数字]\n\
    查询对应bpm所有歌曲\n\n\
⭕[谱面预览+曲名(+难度)]\n\
    查询对应曲名，难度的谱面预览\n\
    ⭐难度支持的输入: easy, normal, hard, expert, master, append, ez, nm, hd, ex, ma, ap, apd\n\
    ⭐如果查询master可省略难度\n\n\
⭕[musicset+昵称+to+歌名]\n\
    设置歌曲昵称\n\
⭕[musicdel+昵称]\n\
    删除歌曲昵称\n\
⭕[charalias+昵称]\n\
    查看特定角色所有昵称\n\
⭕[charaset+昵称+to+角色名/现有昵称]\n\
    设置角色群通用昵称\n\
⭕[charadel+昵称]\n\
    删除角色群通用昵称\n\
⭕[grcharaset+昵称+to+角色名/现有昵称]\n\
    设置仅当前群可用昵称\n\
⭕[grcharadel+昵称]\n\
    删除仅当前群可用昵称")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = ("\
玩家信息相关查询\n\n\
    ⭐在命令前加cn/en/tw/kr即可查询国服/国际服/台服/韩服信息，如cn绑定, twsk, kr逮捕, enpjskprofile\n\n\
⭕[绑定+id]\n\
    通过游戏id绑定你的游戏账号\n\n\
⭕[sk]\n\
    如果你在前100，可以用该命令查询排名和分数\n\
⭕[sk+游戏数字id]\n\
    查询特定游戏玩家的排名和分数\n\
⭕[sk+排名]\n\
    查询特定排名玩家的排名与分数，支持同时查询最多7个玩家\n\
⭕[查房/cf+排名]\n\
    查询特定排名最近1小时相关信息\n\
⭕[sk线]\n\
    查询榜线分数\n\
⭕[时速]\n\
    查看近一小时各榜线的PT增长速度\n\
⭕[半日速]\n\
    查看近半天各榜线的PT增长速度\n\
⭕[日速]\n\
    查看近一天各榜线的PT增长速度\n\
⭕[分数线/rtr+排名]\n\
    查看本期活动中特定排名的分数趋势\n\
⭕[追踪/ptr]\n\
    追踪自己在本期活动中的活动PT趋势与活动排名趋势\n\
⭕[追踪/ptr+排名]\n\
    追踪目前特定排名在本期活动中的活动PT趋势与活动排名趋势\n\
⭕[逮捕]\n\
    查看自己的expert难度、master难度、append难度的fc、ap数\n\
⭕[逮捕@xxx]\n\
    如果此人绑定过id，就可以看TA的ex与master难度fc、ap数\n\
⭕[逮捕+id]\n\
    查看对应uid的expert难度、master难度、append难度的fc、ap数\n\
⭕[pjskprofile/个人信息]\n\
    生成绑定id的profile图片\n\n\
⭕[不给看]\n\
    不允许他人逮捕自己，但自己还是可以逮捕自己，使用sk查分和逮捕自己时不会显示游戏id\n\
⭕[给看]\n\
    允许他人逮捕自己")
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
MySekai相关查询\n\n\
    ⭐在使用该功能前请确保已上传MySekai数据至Haruki数据库，如未上传请按照帮助文档中对应模块进行上传\n\n\
⭕[mysekai_analyze/mysekai分析/ms分析/msa]\n\
    根据用户上传至Haruki数据库的数据分析MySekai现存材料\n\
⭕[mysekai_analyze2/mysekai分析2/ms分析2/msa2]\n\
    根据用户上传至Haruki数据库的数据分析MySekai现存材料 (新版UI设计)\n\
⭕[mysekai_maps/msm/mysekai地图/ms地图]\n\
    根据用户上传至Haruki数据库的数据生成资源分布图\n\
    mysekai_maps指令后添加数字可查询单图地图\n\
    ⭐数字1：草原\n\
    ⭐数字2：花田\n\
    ⭐数字3：沙滩\n\
    ⭐数字4：废墟\n\
⭕[mysekai照片/ms照片/msp+序号]\n\
    根据用户上传到Haruki数据库的数据下载用户在MySekai里面拍摄的照片 (按拍摄顺序)"
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = "\
卡牌及活动信息相关查询\n\n\
⭕[查卡/查卡面/查询卡面/findcard+角色昵称]\n\
    获取当前角色所有卡牌\n\
⭕[查卡/查卡面/查询卡面/cardinfo+卡面id]\n\
    获取卡牌id详细卡面信息\n\
⭕[card+卡面id]\n\
    获取当前卡牌高清图片\n\
⭕[查活动/查询活动/event+活动id]\n\
    查看指定活动信息（可直接使用event查看当前活动信息）\n\
⭕[查活动/查询活动/findevent+关键字]\n\
    通过关键字筛选活动，返回活动概要图，没有关键字则会返回提示图\n\
⭕[活动图鉴/活动列表/活动总览/findevent all]\n\
    返回当前所有活动的概要"
    msg.append({
        "type": "node",
        "data": {
            "name": "Shinonome Ena",
            "uin": bot.self_id,
            "content": text
        }
    })

    text = MessageSegment.text("\
===== bot人设原型 =====\n\
Shinonome Ena 东云绘名\n\
东云绘名（東雲 絵名，しののめ えな）是《世界计划 彩色舞台 feat. 初音未来》（Project SEKAI, PJSK）及其衍生作品的登场角色。代表色为 #ccaa88。")
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



@ena_bottle_help.handle()
async def main(bot: Bot, ev: MessageEvent):
    msg = []

    text = "\
🎨Ena的漂流瓶使用帮助🎨"
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
    可以将自身心愿寄托在漂流瓶中并交给Ena扔进湖里\n"
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
• 每人每天仅有一次机会扔瓶子\n\
• 请勿在漂流瓶中输入不宜内容，一经发现且毫无悔改者做全局拉黑处理"
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
🎨Ena的猜卡面使用帮助🎨"
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
        退出当前的猜卡面游戏\n"
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
• 单次猜卡面回答时间约为30秒\n\
• 回答时请务必引用原区域图片消息\n\
• 支持角色花名核对，所采用花名为Haruki数据库所收录角色花名，更新日期：2025.2.27\n\
• 游戏全流程仅支持本人进行作答"
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
🎨Ena的周边盲抽使用帮助🎨"
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
    （感谢祭系列为四周年感谢祭）\n"
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
• 不支持未收录的周边款式"
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