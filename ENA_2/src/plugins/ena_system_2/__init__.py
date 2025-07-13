# --------------------------
# 导入区域
# --------------------------
from nonebot.plugin import PluginMetadata

from .A import apply_auth, cancel_target_auth, cancel_current_auth, change_user, query_target_auth, query_current_auth, query_by_admin, query_by_user
from .B import add_blacklist, del_blacklist, query_blacklist_list, query_blacklist_user
from .C import open_target_aichat, close_target_aichat, query_target_aichat, open_current_aichat, close_current_aichat, query_current_aichat, query_aichat_group_list


# --------------------------
# 插件系统元信息
# --------------------------
__plugin_meta__ = PluginMetadata(
    name="ena_system_2",
    description="",
    usage=""
)