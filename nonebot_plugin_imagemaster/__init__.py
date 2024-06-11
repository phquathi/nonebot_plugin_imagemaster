from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .bot_main import *

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-imagemaster",
    description="提供多种图像处理功能的插件",
    usage="pip install nonebot-plugin-imagemaster",
    type="application",
    homepage="https://github.com/phquathi/nonebot_plugin_imagemaster",
    config=None,
    supported_adapters={"~onebot.v11"}
)
