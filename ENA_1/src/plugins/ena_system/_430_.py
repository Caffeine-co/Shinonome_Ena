# --------------------------
# 导入区域
# --------------------------
import aiofiles
import json
from datetime import datetime
from pathlib import Path



# --------------------------
# 配置区域
# --------------------------
WHITELIST_PATH = Path(__file__).parent / "resources/use_limit/group_whitelist.json"    # 群白名单路径
AICHAT_WHITELIST_PATH = Path(__file__).parent / "resources/use_limit/aichat_group_whitelist.json"   # ai聊天白名单
BLACKLIST_PATH = Path(__file__).parent / "resources/use_limit/user_blacklist.json"    # 用户黑名单路径
# BLACKLIST_PATH = Path("C:/QQbot/ENANA/src/plugins/user_blacklist.json")

EXEMPT_USER_ID = "2083909754"  # 豁免用户ID

MAX_DAILY_LIMIT_authenticate = 1  # authenticate每日限制次数
MAX_DAILY_LIMIT_blindgoods = 5  # blindgoods每日限制次数
MAX_DAILY_LIMIT_bottles = 1  # bottles每日限制次数
MAX_DAILY_LIMIT_draw_lots = 3  # draw_lots每日限制次数
MAX_DAILY_LIMIT_gacha = 50  # gacha每日限制次数
MAX_DAILY_LIMIT_guessplay = 10  # guessplay每日限制次数

DATA_FILE_authenticate = Path(__file__).parent / "resources/usage_data/usage_data_authenticate.json"
DATA_FILE_blindgoods = Path(__file__).parent / "resources/usage_data/usage_data_blindgoods.json"
DATA_FILE_bottles = Path(__file__).parent / "resources/usage_data/usage_data_bottles.json"
DATA_FILE_draw_lots = Path(__file__).parent / "resources/usage_data/usage_data_draw_lots.json"
DATA_FILE_gacha = Path(__file__).parent / "resources/usage_data/usage_data_gacha.json"
DATA_FILE_guessplay = Path(__file__).parent / "resources/usage_data/usage_data_guessplay.json"



# --------------------------
# 黑白名单检查函数
# --------------------------
# 黑白名单检查函数
# async def check_group_whitelist(group_id: int) -> bool:
#    """群聊白名单检查"""
#    try:
#        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
#            whitelist = json.loads(await f.read())
#            return group_id in whitelist
#    except (FileNotFoundError, json.JSONDecodeError):
#        return False


async def check_group_whitelist(group_id: int) -> bool:
    """群聊白名单检查"""
    try:
        # 使用异步方式读取文件
        async with aiofiles.open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            whitelist = json.loads(content)

            # 从字典列表中提取群号集合
            registered_groups = {entry["group_id"] for entry in whitelist}
            return group_id in registered_groups

    except (FileNotFoundError, json.JSONDecodeError):
        # 文件不存在或格式错误时视为无权限
        return False

    except KeyError:
        # 处理旧数据残留的异常格式
        return False

    except Exception as e:
        print(f"白名单核查异常: {str(e)}")
        return False


async def check_user_blacklist(user_id: int) -> bool:
    """用户黑名单检查"""
    try:
        async with aiofiles.open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
            # content = await f.read()
            # blacklist = json.loads(content)
            blacklist = json.loads(await f.read())
            return user_id in blacklist

    except FileNotFoundError:
        # 文件不存在视为无黑名单
        return False

    except json.JSONDecodeError:
        # 文件格式错误时默认阻止使用
        return True

    except Exception as e:
        #   nonebot.logger.error(f"黑名单检查异常：{str(e)}")
        # 其他异常情况保守处理
        return True


async def check_ai_group_whitelist(group_id: int) -> bool:
    """ai聊天群聊白名单检查"""
    try:
        # 使用异步方式读取文件
        async with aiofiles.open(AICHAT_WHITELIST_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            whitelist = json.loads(content)

            # 从字典列表中提取群号集合
            registered_groups = {entry["group_id"] for entry in whitelist}
            return group_id in registered_groups

    except (FileNotFoundError, json.JSONDecodeError):
        # 文件不存在或格式错误时视为无权限
        return False
    except KeyError:
        # 处理旧数据残留的异常格式
        return False
    except Exception as e:
        print(f"ai聊天白名单核查异常: {str(e)}")
        return False



# --------------------------
# 使用限制检查函数
# --------------------------
async def check_authenticate_usage(user_id: str):
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 异步读取数据
    try:
        async with aiofiles.open(DATA_FILE_authenticate, "r") as f:
            data = json.loads(await f.read())
    except FileNotFoundError:
        data = {}

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_authenticate:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_authenticate, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_blindgoods_usage(user_id: str):
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 异步读取数据
    try:
        async with aiofiles.open(DATA_FILE_blindgoods, "r") as f:
            data = json.loads(await f.read())
    except FileNotFoundError:
        data = {}

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_blindgoods:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_blindgoods, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_bottles_usage(user_id: str):
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # 添加空文件处理逻辑
        async with aiofiles.open(DATA_FILE_bottles, "r") as f:
            try:
                data = json.loads(await f.read())
            except json.JSONDecodeError:
                # 处理空文件情况
                data = {}
    except FileNotFoundError:
        # 文件不存在时创建初始文件
        async with aiofiles.open(DATA_FILE_bottles, "w") as f:
            await f.write(json.dumps({}))
        data = {}

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_bottles:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_bottles, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_draw_lots_usage(user_id: str):
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 异步读取数据
    try:
        async with aiofiles.open(DATA_FILE_draw_lots, "r") as f:
            data = json.loads(await f.read())
    except FileNotFoundError:
        data = {}

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_draw_lots:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_draw_lots, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_gacha_usage_one(user_id: str):
    """每日次数限制检查/单抽"""
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # 添加空文件处理逻辑
        async with aiofiles.open(DATA_FILE_gacha, "r") as f:
            try:
                data = json.loads(await f.read())
            except json.JSONDecodeError:
                # 处理空文件情况
                data = {}
    except FileNotFoundError:
        # 文件不存在时创建初始文件
        async with aiofiles.open(DATA_FILE_gacha, "w") as f:
            await f.write(json.dumps({}))
        data = {}

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_gacha:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_gacha, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_gacha_usage_ten(user_id: str):
    """每日次数限制检查/十连"""
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # 添加空文件处理逻辑
        async with aiofiles.open(DATA_FILE_gacha, "r") as f:
            try:
                data = json.loads(await f.read())
            except json.JSONDecodeError:
                # 处理空文件情况
                data = {}
    except FileNotFoundError:
        # 文件不存在时创建初始文件
        async with aiofiles.open(DATA_FILE_gacha, "w") as f:
            await f.write(json.dumps({}))
        data = {}

    # 检查用户记录
    record = data.get(user_id, {})
    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 10
        update_data = {"date": current_date, "count": new_count}
    else:
        # 次数检查
        new_count = record["count"] + 10
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_gacha:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_gacha, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True


async def check_guessplay_usage(user_id: str):
    # 豁免检查
    if user_id == EXEMPT_USER_ID:
        return True

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # 添加空文件处理逻辑
        async with aiofiles.open(DATA_FILE_guessplay, "r") as f:
            try:
                data = json.loads(await f.read())
            except json.JSONDecodeError:
                # 处理空文件情况
                data = {}

    except FileNotFoundError:
        # 文件不存在时创建初始文件
        async with aiofiles.open(DATA_FILE_guessplay, "w") as f:
            await f.write(json.dumps({}))
        data = {}

    # 检查用户记录
    record = data.get(user_id, {})

    if record.get("date") != current_date:
        # 日期变更则重置
        new_count = 1
        update_data = {"date": current_date, "count": new_count}

    else:
        # 次数检查
        new_count = record["count"] + 1
        update_data = {"date": current_date, "count": new_count}

    # 更新前检查限制
    if new_count > MAX_DAILY_LIMIT_guessplay:
        return False

    # 异步保存更新
    data[user_id] = update_data
    async with aiofiles.open(DATA_FILE_guessplay, "w") as f:
        await f.write(json.dumps(data, indent=2))

    return True