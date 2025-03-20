#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
百度云盘工具类模块

提供对百度云盘进行操作的工具类，封装了百度云盘SDK的常用功能，
包括文件上传、下载、分享、移动、复制、删除等基本功能，
以及目录操作、文件搜索和大文件分片上传等高级功能。
"""

import os
import time
import json
import hashlib
from typing import Dict, List, Optional, Union, Any, Tuple

import requests


class BaiduCloudClient:
    """百度云盘客户端工具类
    
    封装百度云盘API的常用操作，提供简单易用的接口进行云盘文件管理。
    
    Attributes:
        app_key (str): 百度云应用的API Key
        secret_key (str): 百度云应用的Secret Key
        access_token (str): 用户授权访问令牌
        refresh_token (str): 用于刷新access_token的令牌
        token_expire_time (int): access_token的过期时间戳
    """
    
    _BASE_URL = "https://pan.baidu.com"
    _OPENAPI_URL = "https://openapi.baidu.com"
    # API基础URL
    BASE_URL = f"{_BASE_URL}/rest/2.0/xpan"
    OPENAPI_URL = f"{_OPENAPI_URL}/oauth/2.0"
    
    def __init__(self, app_key: str, secret_key: str, access_token: str = None, 
                 refresh_token: str = None, expires_in: int = None, **kwargs):
        """初始化百度云盘客户端
        
        Args:
            app_key: 百度云应用的API Key
            secret_key: 百度云应用的Secret Key
            access_token: 用户授权访问令牌，可选
            refresh_token: 用于刷新access_token的令牌，可选
            expires_in: token过期时间（秒），可选
        """
        self.app_key = app_key
        self.secret_key = secret_key
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expire_time = int(time.time()) + expires_in if expires_in else 0
        self._session = requests.Session()
    
    def _check_token(self):
        """检查token是否有效，如果无效且有refresh_token，则刷新token"""
        if not self.access_token:
            raise ValueError("未设置access_token，请先获取授权")
        
        # 如果token即将过期且有refresh_token，则刷新token
        current_time = int(time.time())
        if self.token_expire_time > 0 and current_time >= self.token_expire_time - 60 and self.refresh_token:
            self.refresh_access_token()
    
    def get_auth_url(self, redirect_uri: str, scope: str = "basic,netdisk") -> str:
        """获取用户授权链接
        
        Args:
            redirect_uri: 授权回调地址
            scope: 授权权限范围，默认为basic,netdisk
            
        Returns:
            str: 用户授权链接
        """
        params = {
            "client_id": self.app_key,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.OPENAPI_URL}/authorize?{query_string}"
    
    def get_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """通过授权码获取访问令牌
        
        Args:
            code: 授权码
            redirect_uri: 授权回调地址，必须与获取授权码时一致
            
        Returns:
            Dict: 包含access_token、refresh_token等信息的字典
        """
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.app_key,
            "client_secret": self.secret_key,
            "redirect_uri": redirect_uri
        }
        response = self._session.get(f"{self.OPENAPI_URL}/token", params=params)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self.refresh_token = result.get("refresh_token")
            # 设置token过期时间
            if "expires_in" in result:
                self.token_expire_time = int(time.time()) + result["expires_in"]
        
        return result
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """刷新访问令牌
        
        Returns:
            Dict: 包含新的access_token等信息的字典
        """
        if not self.refresh_token:
            raise ValueError("未设置refresh_token，无法刷新token")
        
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.app_key,
            "client_secret": self.secret_key
        }
        response = self._session.get(f"{self.OPENAPI_URL}/token", params=params)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            if "refresh_token" in result:
                self.refresh_token = result["refresh_token"]
            # 更新token过期时间
            if "expires_in" in result:
                self.token_expire_time = int(time.time()) + result["expires_in"]
        
        return result
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息
        
        Returns:
            Dict: 用户信息字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        response = self._session.get(f"{self.BASE_URL}/nas?method=uinfo", params=params)
        return response.json()
    
    def get_quota(self) -> Dict[str, Any]:
        """获取用户空间配额信息
        
        Returns:
            Dict: 包含空间使用情况的字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        response = self._session.get(f"{self._BASE_URL}/api/quota", params=params)
        return response.json()
    
    def list_files(self, dir_path: str = "/", order: str = "name", desc: bool = False, 
                  start: int = 0, limit: int = 1000) -> Dict[str, Any]:
        """获取目录下的文件列表
        
        Args:
            dir_path: 目录路径，默认为根目录
            order: 排序字段，可选值: time（修改时间）, name（文件名）, size（文件大小）
            desc: 是否降序排序
            start: 起始位置，用于分页
            limit: 返回条目数量，默认为1000
            
        Returns:
            Dict: 包含文件列表的字典
        """
        self._check_token()
        params = {
            "access_token": self.access_token,
            "dir": dir_path,
            "order": order,
            "desc": 1 if desc else 0,
            "start": start,
            "limit": limit
        }
        response = self._session.get(f"{self.BASE_URL}/file?method=list", params=params)
        return response.json()
    
    def search_files(self, keyword: str, dir_path: str = "/", recursive: bool = True) -> Dict[str, Any]:
        """搜索文件
        
        Args:
            keyword: 搜索关键词
            dir_path: 搜索目录，默认为根目录
            recursive: 是否递归搜索子目录
            
        Returns:
            Dict: 包含搜索结果的字典
        """
        self._check_token()
        params = {
            "access_token": self.access_token,
            "key": keyword,
            "dir": dir_path,
            "recursion": 1 if recursive else 0
        }
        response = self._session.get(f"{self.BASE_URL}/file?method=search", params=params)
        return response.json()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件信息字典
        """
        self._check_token()
        # 先获取文件的fsid
        list_params = {
            "access_token": self.access_token,
            "dir": os.path.dirname(file_path),
            "limit": 1000
        }
        list_response = self._session.get(f"{self.BASE_URL}/file?method=list", params=list_params)
        list_result = list_response.json()
        
        # 查找文件的fsid
        fsid = None
        if "list" in list_result:
            for file_info in list_result["list"]:
                if file_info.get("path") == file_path:
                    fsid = file_info.get("fs_id")
                    break
        
        if not fsid:
            return {"errno": 1, "errmsg": "File not found"}
        
        # 使用fsid获取文件信息
        params = {
            "access_token": self.access_token,
            "fsids": f"[{fsid}]"
        }
        response = self._session.get(f"{self.BASE_URL}/multimedia?method=filemetas", params=params)
        return response.json()
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """创建目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            Dict: 创建结果字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        data = {"path": dir_path}
        response = self._session.post(f"{self.BASE_URL}/file?method=create", 
                               params=params, data=data)
        return response.json()
    
    def delete_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """删除文件或目录
        
        Args:
            file_paths: 文件或目录路径列表
            
        Returns:
            Dict: 删除结果字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_paths)}
        response = self._session.post(f"{self.BASE_URL}/file?method=filemanager&opera=delete", 
                               params=params, data=data)
        return response.json()
    
    def rename_file(self, file_path: str, new_name: str) -> Dict[str, Any]:
        """重命名文件或目录
        
        Args:
            file_path: 文件或目录路径
            new_name: 新名称
            
        Returns:
            Dict: 重命名结果字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        data = {
            "filelist": json.dumps([{"path": file_path, "newname": new_name}])
        }
        response = self._session.post(f"{self.BASE_URL}/file?method=filemanager&opera=rename", 
                               params=params, data=data)
        return response.json()
    
    def move_files(self, file_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """移动文件或目录
        
        Args:
            file_list: 文件移动列表，格式为[{"path":"源路径", "dest":"目标路径"},...]            
        Returns:
            Dict: 移动结果字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_list)}
        response = self._session.post(f"{self.BASE_URL}/file?method=filemanager&opera=move", 
                               params=params, data=data)
        return response.json()
    
    def copy_files(self, file_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """复制文件或目录
        
        Args:
            file_list: 文件复制列表，格式为[{"path":"源路径", "dest":"目标路径"},...]
            
        Returns:
            Dict: 复制结果字典
        """
        self._check_token()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_list)}
        response = self._session.post(f"{self.BASE_URL}/file?method=filemanager&opera=copy", 
                               params=params, data=data)
        return response.json()
    
    def get_download_link(self, file_path: str) -> str:
        """获取文件下载链接
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件下载链接
        """
        self._check_token()
        # 直接使用下载API获取下载链接
        params = {
            "access_token": self.access_token,
            "path": file_path
        }
        print(f"开始下载文件: {file_path} 到 {local_path}")
        response = self._session.get(f"{self.BASE_URL}/file?method=download", params=params)
        if response.status_code != 200:
            print(f"下载请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return False
        
        # 解析响应获取下载链接
        try:
            # 检查响应内容是否为JSON格式
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                result = response.json()
                # 检查错误码
                if 'errno' in result and result['errno'] != 0:
                    print(f"获取下载链接失败，错误码: {result['errno']}，错误信息: {result.get('errmsg', '未知错误')}")
                    return False
                
                download_link = result.get("dlink", "")
                if not download_link:
                    print(f"获取下载链接失败: {result}")
                    return False
                else:
                    # 如果不是JSON格式，可能是直接返回了文件内容（这是正常情况）
                    # 直接将响应内容写入文件
                    try:
                        # 确保目录存在
                        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                        
                        print(f"直接接收到文件内容，文件大小: {len(response.content)/1024:.2f}KB")
                        # 直接写入文件
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        print(f"文件下载成功: {local_path}")
                        return True
                    except Exception as e:
                        print(f"写入文件失败: {str(e)}")
                        return False
        except Exception as e:
            print(f"解析下载链接失败: {str(e)}")
            return False
            
        # 使用下载链接获取文件内容
        print(f"使用下载链接获取文件内容: {download_link}")
        download_response = self._session.get(download_link, stream=True)
        if download_response.status_code != 200:
            print(f"下载请求失败，状态码: {download_response.status_code}, 响应内容: {download_response.text}")
            return False
        
        # 获取文件大小
        file_size = int(download_response.headers.get('Content-Length', 0))
        print(f"开始下载文件，总大小: {file_size/1024/1024:.2f}MB")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        
        # 分块下载文件
        downloaded_size = 0
        last_percent = 0
        with open(local_path, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # 每增加5%报告一次进度
                    percent = int(downloaded_size * 100 / file_size) if file_size > 0 else 0
                    if percent >= last_percent + 5 or percent == 100:
                        print(f"下载进度: {percent}% ({downloaded_size/1024/1024:.2f}MB/{file_size/1024/1024:.2f}MB)")
                        last_percent = percent
        
        print(f"文件下载完成: {local_path}")
        return True
    
    def download_file(self, file_path: str, local_path: str, chunk_size: int = 1024 * 1024) -> bool:
        """下载文件到本地
        
        Args:
            file_path: 云盘文件路径
            local_path: 本地保存路径
            chunk_size: 分块下载的块大小，默认1MB
            
        Returns:
            bool: 下载是否成功
        """
        self._check_token()
        try:
            # 直接使用下载API获取下载链接
            params = {
                "access_token": self.access_token,
                "path": file_path
            }
            print(f"开始下载文件: {file_path} 到 {local_path}")
            response = self._session.get(f"{self.BASE_URL}/file?method=download", params=params)
            if response.status_code != 200:
                print(f"下载请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
            
            # 解析响应获取下载链接
            # 检查响应内容是否为JSON格式
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                result = response.json()
                # 检查错误码
                if 'errno' in result and result['errno'] != 0:
                    print(f"获取下载链接失败，错误码: {result['errno']}，错误信息: {result.get('errmsg', '')}")
                    return False
                
                download_link = result.get("dlink", "")
                if not download_link:
                    print(f"获取下载链接失败: {result}")
                    return False
                
                # 使用下载链接获取文件内容
                print(f"获取到下载链接，正在下载文件...")
                download_response = self._session.get(download_link, stream=True)
                if download_response.status_code != 200:
                    print(f"使用下载链接下载失败，状态码: {download_response.status_code}")
                    return False
                
                # 确保目录存在
                os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                
                # 分块写入文件
                with open(local_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                # 如果不是JSON格式，可能是直接返回了文件内容（这是正常情况）
                # 直接将响应内容写入文件
                try:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                    
                    # 直接写入文件
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    return True
                except Exception as e:
                    print(f"写入文件失败: {e}")
                    return False
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str, ondup: str = "overwrite") -> Dict[str, Any]:
        """上传文件到百度云盘
        
        Args:
            local_path: 本地文件路径
            remote_path: 云盘保存路径
            ondup: 重名文件处理策略，可选值: overwrite(覆盖), newcopy(创建副本)
            
        Returns:
            Dict: 上传结果字典
        """
        self._check_token()
        
        # 检查文件是否存在
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"文件不存在: {local_path}")
        
        # 获取文件大小
        file_size = os.path.getsize(local_path)
        
        # 如果文件大于4MB，使用分片上传
        if file_size > 4 * 1024 * 1024:
            return self._upload_large_file(local_path, remote_path, ondup)
        
        # 小文件直接上传
        return self._upload_small_file(local_path, remote_path, ondup)
    
    def _upload_small_file(self, local_path: str, remote_path: str, ondup: str) -> Dict[str, Any]:
        """上传小文件（小于4MB）
        
        Args:
            local_path: 本地文件路径
            remote_path: 云盘保存路径
            ondup: 重名文件处理策略
            
        Returns:
            Dict: 上传结果字典
        """
        params = {
            "access_token": self.access_token,
            "path": remote_path,
            "ondup": ondup
        }
        
        with open(local_path, 'rb') as f:
            files = {'file': f}
            response = self._session.post(
                f"{self.BASE_URL}/file?method=upload",
                params=params,
                files=files
            )
        
        return response.json()
    
    def _upload_large_file(self, local_path: str, remote_path: str, ondup: str) -> Dict[str, Any]:
        """分片上传大文件（大于4MB）
        
        Args:
            local_path: 本地文件路径
            remote_path: 云盘保存路径
            ondup: 重名文件处理策略
            
        Returns:
            Dict: 上传结果字典
        """
        try:
            # 获取文件大小
            file_size = os.path.getsize(local_path)
            
            # 计算文件MD5
            md5 = self._calculate_file_md5(local_path)
            print(f"开始上传文件: {remote_path}, 大小: {file_size/1024/1024:.2f}MB, MD5: {md5}")
            
            # 预创建文件
            precreate_result = self._precreate_file(remote_path, file_size, md5, ondup)
            if 'errno' in precreate_result and precreate_result['errno'] != 0:
                print(f"预创建文件失败: 错误码 {precreate_result.get('errno')}, 错误信息: {precreate_result.get('errmsg', '未知错误')}")
                return precreate_result
            
            # 获取上传ID
            upload_id = precreate_result.get('uploadid', '')
            if not upload_id:
                error_result = {"errno": -1, "errmsg": "获取上传ID失败"}
                print(f"获取上传ID失败: {precreate_result}")
                return error_result
            
            print(f"获取上传ID成功: {upload_id}, 开始分片上传...")
            # 分片上传
            block_list = []
            chunk_size = 4 * 1024 * 1024  # 4MB
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            with open(local_path, 'rb') as f:
                block_index = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 上传分片
                    print(f"上传分片 {block_index+1}/{total_chunks} ({len(chunk)/1024/1024:.2f}MB)...")
                    result = self._upload_chunk(chunk, remote_path, upload_id, block_index)
                    if 'errno' in result and result['errno'] != 0:
                        print(f"上传分片 {block_index+1}/{total_chunks} 失败: 错误码 {result.get('errno')}, 错误信息: {result.get('errmsg', '未知错误')}")
                        return result
                    
                    # 记录分片MD5
                    chunk_md5 = hashlib.md5(chunk).hexdigest()
                    block_list.append(chunk_md5)
                    print(f"分片 {block_index+1}/{total_chunks} 上传成功, MD5: {chunk_md5}")
                    block_index += 1
            
            # 创建文件
            print(f"所有分片上传完成，共 {len(block_list)} 个分片，正在创建文件...")
            create_result = self._create_file(remote_path, file_size, upload_id, block_list, ondup)
            if 'errno' in create_result and create_result['errno'] != 0:
                print(f"创建文件失败: 错误码 {create_result.get('errno')}, 错误信息: {create_result.get('errmsg', '未知错误')}")
            else:
                print(f"文件上传成功: {remote_path}, 文件ID: {create_result.get('fs_id')}")
            
            return create_result
        except Exception as e:
            error_result = {"errno": -1, "errmsg": f"上传文件异常: {str(e)}"}
            print(f"上传文件异常: {e}")
            return error_result
    
    def _calculate_file_md5(self, file_path: str) -> str:
        """计算文件MD5值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件MD5值
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _precreate_file(self, remote_path: str, file_size: int, md5: str, ondup: str) -> Dict[str, Any]:
        """预创建文件
        
        Args:
            remote_path: 云盘保存路径
            file_size: 文件大小
            md5: 文件MD5值
            ondup: 重名文件处理策略
            
        Returns:
            Dict: 预创建结果字典
        """
        # 计算分片数量和分片大小
        chunk_size = 4 * 1024 * 1024  # 4MB
        block_count = (file_size + chunk_size - 1) // chunk_size
        
        # 预计算分片MD5列表（空列表，实际上传时会计算）
        block_list = ["" for _ in range(block_count)]
        
        params = {"access_token": self.access_token}
        data = {
            "path": remote_path,
            "size": file_size,
            "isdir": 0,
            "autoinit": 1,
            "rtype": 1,  # 上传类型，1表示上传文件（修正：从3改为1）
            "block_list": json.dumps(block_list),  # 提供预计算的分片列表
            "ondup": ondup
        }
        
        response = self._session.post(
            f"{self.BASE_URL}/file?method=precreate",
            params=params,
            data=data
        )
        
        result = response.json()
        if 'errno' in result and result['errno'] != 0:
            print(f"预创建文件失败，错误码: {result['errno']}，错误信息: {result.get('errmsg', '')}")
        
        return result
    
    def _upload_chunk(self, chunk: bytes, remote_path: str, upload_id: str, block_index: int) -> Dict[str, Any]:
        """上传文件分片
        
        Args:
            chunk: 文件分片数据
            remote_path: 云盘保存路径
            upload_id: 上传ID
            block_index: 分片索引
            
        Returns:
            Dict: 上传分片结果字典
        """
        params = {
            "access_token": self.access_token,
            "path": remote_path,
            "uploadid": upload_id,
            "partseq": block_index,  # 分片索引，从0开始
            "type": "tmpfile"  # 添加type参数，指定为临时文件
        }
        
        files = {'file': chunk}
        response = self._session.post(
            "https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?method=upload",
            params=params,
            files=files
        )
        
        return response.json()
    
    def _create_file(self, remote_path: str, file_size: int, upload_id: str, 
                    block_list: List[str], ondup: str) -> Dict[str, Any]:
        """创建文件（完成分片上传）
        
        Args:
            remote_path: 云盘保存路径
            file_size: 文件大小
            upload_id: 上传ID
            block_list: 分片MD5列表
            ondup: 重名文件处理策略
            
        Returns:
            Dict: 创建文件结果字典
        """
        params = {"access_token": self.access_token}
        data = {
            "path": remote_path,
            "size": file_size,
            "isdir": 0,
            "uploadid": upload_id,
            "block_list": json.dumps(block_list),
            "rtype": 3  # 上传类型，3表示合并分片文件
        }        
        response = self._session.post(
            f"{self.BASE_URL}/file?method=create",
            params=params,
            data=data
        )
        
        return response.json()