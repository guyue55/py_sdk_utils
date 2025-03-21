#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
百度云盘工具类测试模块

本模块包含对BaiduCloudClient类的单元测试，
使用mock技术模拟百度云API的响应，测试各种功能的正确性。
"""

import os
import sys
import time
import json
import unittest
from unittest import mock
import hashlib
import tempfile

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sdk_utils.baidu_cloud import BaiduCloudClient


class TestBaiduCloudClient(unittest.TestCase):
    """百度云盘客户端测试类"""

    def setUp(self):
        """测试前准备工作"""
        self.app_key = "test_app_key"
        self.secret_key = "test_secret_key"
        self.access_token = "test_access_token"
        self.refresh_token = "test_refresh_token"
        self.redirect_uri = "http://localhost/callback"
        
        # 创建客户端实例
        self.client = BaiduCloudClient(
            app_key=self.app_key,
            secret_key=self.secret_key,
            access_token=self.access_token,
            refresh_token=self.refresh_token
        )
        
        # 创建临时目录用于测试文件操作
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理工作"""
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        client = BaiduCloudClient(self.app_key, self.secret_key)
        self.assertEqual(client.app_key, self.app_key)
        self.assertEqual(client.secret_key, self.secret_key)
        self.assertIsNone(client.access_token)
        self.assertIsNone(client.refresh_token)
        
        client = BaiduCloudClient(
            app_key=self.app_key,
            secret_key=self.secret_key,
            access_token=self.access_token,
            refresh_token=self.refresh_token
        )
        self.assertEqual(client.access_token, self.access_token)
        self.assertEqual(client.refresh_token, self.refresh_token)
    
    def test_get_auth_url(self):
        """测试获取授权URL"""
        auth_url = self.client.get_auth_url(self.redirect_uri)
        expected_url = (
            f"https://openapi.baidu.com/oauth/2.0/authorize?"
            f"client_id={self.app_key}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope=basic,netdisk"
        ).replace(" ", "")
        
        # 移除URL中的空格后比较
        self.assertEqual(auth_url.replace(" ", ""), expected_url)
        
        # 测试自定义scope
        custom_scope = "basic"
        auth_url = self.client.get_auth_url(self.redirect_uri, scope=custom_scope)
        expected_url = (
            f"https://openapi.baidu.com/oauth/2.0/authorize?"
            f"client_id={self.app_key}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={custom_scope}"
        ).replace(" ", "")
        self.assertEqual(auth_url.replace(" ", ""), expected_url)
    
    @mock.patch('requests.Session.get')
    def test_get_access_token(self, mock_get):
        """测试获取访问令牌"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 2592000
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        code = "test_auth_code"
        result = self.client.get_access_token(code, self.redirect_uri)
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        self.assertEqual(self.client.access_token, "new_access_token")
        self.assertEqual(self.client.refresh_token, "new_refresh_token")
        self.assertGreater(self.client.token_expire_time, int(time.time()))
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://openapi.baidu.com/oauth/2.0/token")
        self.assertEqual(kwargs['params']['grant_type'], "authorization_code")
        self.assertEqual(kwargs['params']['code'], code)
        self.assertEqual(kwargs['params']['client_id'], self.app_key)
        self.assertEqual(kwargs['params']['client_secret'], self.secret_key)
        self.assertEqual(kwargs['params']['redirect_uri'], self.redirect_uri)
    
    @mock.patch('requests.Session.get')
    def test_refresh_access_token(self, mock_get):
        """测试刷新访问令牌"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "refresh_token": "refreshed_refresh_token",
            "expires_in": 2592000
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.client.refresh_access_token()
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        self.assertEqual(self.client.access_token, "refreshed_access_token")
        self.assertEqual(self.client.refresh_token, "refreshed_refresh_token")
        self.assertGreater(self.client.token_expire_time, int(time.time()))
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://openapi.baidu.com/oauth/2.0/token")
        self.assertEqual(kwargs['params']['grant_type'], "refresh_token")
        self.assertEqual(kwargs['params']['refresh_token'], self.refresh_token)
        self.assertEqual(kwargs['params']['client_id'], self.app_key)
        self.assertEqual(kwargs['params']['client_secret'], self.secret_key)
    
    @mock.patch('requests.Session.get')
    def test_get_user_info(self, mock_get):
        """测试获取用户信息"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "baidu_name": "测试用户",
            "netdisk_name": "测试网盘",
            "uk": 12345678,
            "vip_type": 1
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.client.get_user_info()
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://pan.baidu.com/rest/2.0/xpan/nas?method=uinfo")
        self.assertEqual(kwargs['params']['access_token'], self.access_token)
    
    @mock.patch('requests.Session.get')
    def test_get_quota(self, mock_get):
        """测试获取空间配额信息"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "total": 2199023255552,  # 2TB
            "used": 5368709120,      # 5GB
            "free": 2193654546432    # 剩余空间
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.client.get_quota()
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://pan.baidu.com/api/quota")
        self.assertEqual(kwargs['params']['access_token'], self.access_token)
    
    @mock.patch('requests.Session.get')
    def test_list_files(self, mock_get):
        """测试获取文件列表"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "list": [
                {
                    "fs_id": 123456789,
                    "path": "/测试文件.txt",
                    "server_filename": "测试文件.txt",
                    "size": 1024,
                    "isdir": 0,
                    "ctime": 1600000000,
                    "mtime": 1600000000
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.client.list_files("/")
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://pan.baidu.com/rest/2.0/xpan/file?method=list")
        self.assertEqual(kwargs['params']['access_token'], self.access_token)
        self.assertEqual(kwargs['params']['dir'], "/")
    
    @mock.patch('requests.Session.post')
    def test_delete_files(self, mock_post):
        """测试删除文件"""
        # 模拟API响应
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "info": []
        }
        mock_post.return_value = mock_response
        
        # 调用方法
        file_paths = ["/测试文件.txt", "/测试目录"]
        result = self.client.delete_files(file_paths)
        
        # 验证结果
        self.assertEqual(result, mock_response.json.return_value)
        
        # 验证请求参数
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=delete")
        self.assertEqual(kwargs['params']['access_token'], self.access_token)
        self.assertEqual(json.loads(kwargs['data']['filelist']), file_paths)


if __name__ == "__main__":
    unittest.main()