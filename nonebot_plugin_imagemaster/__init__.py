from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-imagemaster",
    description="提供多种图像处理功能的插件",
    usage="",
    type="application",
    homepage="https://github.com/phquathi/nonebot_plugin_imagemaster",
    config=None,
    supported_adapters={"~onebot.v11"}
)
