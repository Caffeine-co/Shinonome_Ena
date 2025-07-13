# --------------------------
# 导入区域
# --------------------------
from nonebot.plugin import PluginMetadata

from .A import ai_chat, balance_query, reset_chat
from .B import authenticate
from .C import draw_goods
from .D import throw_bottle, pick_bottle, delete_bottle, view_bottle
from .E import calculate_power, calculate_together_score, calculate_solo_score, calculate_challenge_score
from .F import choose
from .G import sign, query_sign
from .H import double_click
from .I import draw_lots
from .J import gacha_ord_one, gacha_ord_ten, gacha_lim_one, gacha_lim_ten, gacha_birth_one, gacha_birth_ten
from .K import guess_character, guess_music, reply_matcher
from .L import ena_help, ena_admin_help, ena_aichat_help, ena_blindgoods_help, ena_bottle_help, ena_gacha_help, ena_guessplay_help, ena_calculator_help, ena_pjsk_help, ena_sign_help


# --------------------------
# 插件系统元信息
# --------------------------
__plugin_meta__ = PluginMetadata(
    name="ena_system",
    description="",
    usage=""
)