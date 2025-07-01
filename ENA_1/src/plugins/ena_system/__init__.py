# --------------------------
# 导入区域
# --------------------------
# from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

# from .config import Config
from .A import ai_chat, balance_query, reset_chat
from .B import authenticate_reply
from .C import draw_handler
from .D import throw_bottle, pick_bottle, delete_bottle, view_bottle
from .E import calculator_power, calculator_together_score, calculator_solo_score, calculator_challenge_score
from .F import chooser
from .G import sign_cmd, query_cmd
from .H import poke_notice
from .I import lots_drawing
from .J import gacha_ord_one, gacha_ord_ten, gacha_lim_one, gacha_lim_ten, gacha_birth_one, gacha_birth_ten
from .K import guessplay_character, guessplay_music, reply_matcher
from .L import ena_help, ena_pjsk_help, ena_sign_help, ena_bottle_help, ena_aichat_help, ena_guessplay_help, ena_gacha_help, ena_calculator_help, ena_blindgoods_help, ena_admin_help



# --------------------------
# 插件系统元信息
# --------------------------
__plugin_meta__ = PluginMetadata(
    name="ena_system",
    description="",
    usage=""
    # config=Config,
)

# config = get_plugin_config(Config)

