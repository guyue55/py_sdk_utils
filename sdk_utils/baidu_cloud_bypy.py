#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
百度云盘工具类模块

提供对百度云盘进行操作的工具类，封装了百度云盘SDK的常用功能，
包括文件上传、下载、分享、移动、复制、删除等基本功能，
以及目录操作、文件搜索和大文件分片上传等高级功能。
"""

from bypy import ByPy
import os

class BaiduPanTools:
    def __init__(self):
        """初始化并完成OAuth授权"""
        self.bp = ByPy()
        # self._check_auth()

    def _check_auth(self):
        """检查授权状态"""
        if not self.bp.oauth_result:
            print("请访问以下链接完成授权：")
            self.bp.get_auth_url()
            code = input("请输入授权码：")
            self.bp.auth(code)
    
    def upload_file(self, local_path, remote_path=None):
        """
        上传单个文件
        :param local_path: 本地文件路径
        :param remote_path: 云端路径（默认同名存储）
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"本地文件不存在：{local_path}")
        
        remote_name = os.path.basename(local_path) if not remote_path else remote_path
        return self.bp.upload(localpath=local_path, remotepath=remote_name)

    def download_file(self, remote_path, local_dir=None):
        """
        下载单个文件
        :param remote_path: 云端文件路径
        :param local_dir: 本地存储目录（默认当前目录）
        """
        local_path = os.path.join(local_dir or os.getcwd(), os.path.basename(remote_path))
        return self.bp.download(remotepath=remote_path, localpath=local_path)

    def list_files(self, remote_dir="/"):
        """获取指定目录文件列表"""
        return self.bp.list(remote_dir)

    def sync_folder(self, local_folder, remote_folder=None):
        """
        同步本地文件夹到云端
        :param local_folder: 本地文件夹路径
        :param remote_folder: 云端目标文件夹名
        """
        return self.bp.syncup(localdir=local_folder, remotedir=remote_folder)

# 使用示例
if __name__ == "__main__":
    pan = BaiduPanTools()
    
    # 上传文件示例
    pan.upload_file("test_upload.txt")
    
    # 下载文件示例
    pan.download_file("test_upload.txt", "downloads")
    
    # 查看文件列表
    print(pan.list_files())