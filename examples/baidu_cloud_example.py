#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
百度云盘工具类使用示例

本示例展示了如何使用BaiduCloudClient类进行百度云盘操作，
包括授权认证、文件上传下载、目录管理和文件分享等功能。
"""

import os
import sys
import time
import http.server
import socketserver
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sdk_utils.baidu_cloud import BaiduCloudClient

# 全局变量存储授权码
auth_code = None

# 创建一个简单的HTTP服务器来接收授权回调
class AuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        # 解析URL中的授权码
        query = urlparse(self.path).query
        query_components = parse_qs(query)
        if 'code' in query_components:
            auth_code = query_components['code'][0]
            # 返回成功页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><head><title>Authorization Success</title></head>")
            self.wfile.write(b"<body><h1>Authorization Success!</h1>")
            self.wfile.write(b"<p>You have successfully authorized. Please return to the command line.</p>")
            self.wfile.write(b"</body></html>")
            print("\n授权码已接收，您可以关闭浏览器页面并返回命令行。")
        else:
            # 返回错误页面
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><head><title>Authorization Failed</title></head>")
            self.wfile.write(b"<body><h1>Authorization Failed!</h1>")
            self.wfile.write(b"<p>Failed to get authorization code. Please try again.</p>")
            self.wfile.write(b"</body></html>")

    def log_message(self, format, *args):
        # 禁止输出HTTP请求日志
        return


def start_auth_server(port=8000):
    """启动授权回调服务器"""
    handler = AuthCallbackHandler
    httpd = socketserver.TCPServer(("localhost", port), handler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return httpd


def auth_example():
    """授权认证示例"""
    params = {}

    # 创建客户端实例
    client = BaiduCloudClient(
        # app_key="q8WE4EpCsau1oS0MplgMKNBn",
        app_key= "Iv7m0AmGpdGcfpvrDwnme9WpvhtXzXUC",
        secret_key="xxxx",
        **params
    )
    
    # 启动授权回调服务器
    callback_port = 8000
    redirect_uri = f"http://localhost:{callback_port}/callback"
    # httpd = start_auth_server(callback_port)
    
    redirect_uri = "oob"
    # 获取授权URL
    auth_url = client.get_auth_url(redirect_uri=redirect_uri)
    print(f"正在打开浏览器进行授权...")
    print(f"如果浏览器没有自动打开，请手动访问以下链接:\n{auth_url}")
    
    # # 自动打开浏览器
    # webbrowser.open(auth_url)
    
    # # 等待授权码
    # print("等待授权中...")
    # while auth_code is None:
    #     time.sleep(1)
    
    # # 关闭服务器
    # httpd.shutdown()
    
    # # 通过授权码获取access_token
    # print(f"\n已获取授权码，正在获取access_token...")
    # result = client.get_access_token(auth_code, redirect_uri=redirect_uri)
    # print(f"授权结果: {result}")
    
    # 获取用户信息
    user_info = client.get_user_info()
    print(f"用户信息: {user_info}")
    
    # 获取空间配额信息
    quota_info = client.get_quota()
    print(f"空间配额信息: {quota_info}")
    
    return client


def file_management_example(client):
    """文件管理示例
    
    演示如何使用BaiduCloudClient进行文件管理操作，包括：
    - 列出文件
    - 创建目录
    - 搜索文件
    - 重命名文件
    - 删除文件
    """
    # 列出根目录文件
    files = client.list_files("/")
    print(f"根目录文件列表: {str(files)[:200]}...")
    
    # 创建目录
    dir_name = f"/测试目录_{int(time.time())}"
    result = client.create_directory(dir_name)
    print(f"创建目录结果: {result}")
    
    # 搜索文件
    search_result = client.search_files("测试")
    print(f"搜索结果: {str(search_result)[:200]}...")
    
    # 重命名目录
    new_dir_name = f"{dir_name}_renamed"
    rename_result = client.rename_file(dir_name, new_dir_name.split('/')[-1])
    print(f"重命名结果: {rename_result}")
    
    # 删除目录
    delete_result = client.delete_files([new_dir_name])
    print(f"删除结果: {delete_result}")


def upload_download_example(client):
    """上传下载示例
    
    演示如何使用BaiduCloudClient进行文件上传和下载操作
    """
    # 创建测试文件
    local_file = "test_upload.txt"
    with open(local_file, "w", encoding="utf-8") as f:
        f.write("这是一个测试文件，用于测试百度云盘上传功能。" * 10)
    
    # 上传文件
    remote_path = "/test_upload.txt"
    print("正在上传文件...")
    upload_result = client.upload_file(local_file, remote_path)
    print(f"上传结果: {upload_result}")
    
    # 获取文件信息
    file_info = client.get_file_info(remote_path)
    print(f"文件信息: {file_info}")
    
    # 下载文件
    download_path = "test_download.txt"
    print("正在下载文件...")
    download_success = client.download_file(remote_path, download_path)
    print(f"下载结果: {'成功' if download_success else '失败'}")
    
    # 清理本地文件
    os.remove(local_file)
    if os.path.exists(download_path):
        os.remove(download_path)
    
    # 删除远程文件
    client.delete_files([remote_path])


def large_file_example(client):
    """大文件上传示例
    
    演示如何使用BaiduCloudClient进行大文件上传和下载操作
    """
    # 创建大文件（5MB）
    large_file = "large_test_file.bin"
    file_size = 5 * 1024 * 1024  # 5MB
    
    print(f"创建{file_size/1024/1024:.1f}MB测试文件...")
    with open(large_file, "wb") as f:
        f.write(os.urandom(file_size))  # 随机数据
    
    # 上传大文件（会自动使用分片上传）
    remote_path = "/large_test_file.bin"
    print("开始上传大文件...")
    start_time = time.time()
    upload_result = client.upload_file(large_file, remote_path)
    end_time = time.time()
    print(f"大文件上传结果: {upload_result}")
    print(f"上传耗时: {end_time - start_time:.2f}秒")
    
    # 下载大文件
    download_path = "large_test_download.bin"
    print("开始下载大文件...")
    start_time = time.time()
    download_success = client.download_file(remote_path, download_path)
    end_time = time.time()
    print(f"大文件下载结果: {'成功' if download_success else '失败'}")
    print(f"下载耗时: {end_time - start_time:.2f}秒")
    
    # 清理
    os.remove(large_file)
    if os.path.exists(download_path):
        os.remove(download_path)
    client.delete_files([remote_path])


def main():
    print("百度云盘工具类使用示例")
    print("-" * 50)
    
    try:
        # 授权示例
        client = auth_example()
        
        # 文件管理示例
        file_management_example(client)
        
        # 上传下载示例
        upload_download_example(client)
        
        # 大文件示例
        large_file_example(client)
        
        print("\n所有示例执行完毕!")
    except Exception as e:
        print(f"示例执行出错: {e}")
    except KeyboardInterrupt:
        print("\n程序被用户中断")


if __name__ == "__main__":
    main()