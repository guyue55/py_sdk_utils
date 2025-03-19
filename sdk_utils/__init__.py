"""SDK Utils - 一个用于SDK开发的工具库

本包提供构建Python SDK的通用功能，目前主要封装了百度云盘的常用操作，
使开发者能够轻松地在自己的应用中集成百度云盘功能。

主要模块：
- baidu_cloud: 百度云盘API客户端，提供完整的百度云盘操作功能
- baidu_cloud_bypy: 基于bypy库的百度云盘工具，提供简化的操作接口
"""

__version__ = "0.1.0"
__author__ = "Guyue"
__email__ = "guyuecw@qq.com"

# 导出主要类，方便用户直接导入
from .baidu_cloud import BaiduCloudClient
from .baidu_cloud_bypy import BaiduPanTools