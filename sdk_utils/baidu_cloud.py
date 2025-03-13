"""百度云盘工具类模块

提供对百度云盘进行操作的工具类，封装了百度云盘SDK的常用功能，
包括文件上传、下载、分享、移动、复制、删除等基本功能，
以及目录操作、文件搜索和大文件分片上传等高级功能。
"""

import os
import time
import json
import hashlib
from typing import Dict, List, Optional, Union, Callable, BinaryIO, Any, Tuple

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
    
    def __init__(self, app_key: str, secret_key: str, access_token: str = None, 
                 refresh_token: str = None, auto_refresh: bool = True):
        """初始化百度云盘客户端
        
        Args:
            app_key: 百度云应用的API Key
            secret_key: 百度云应用的Secret Key
            access_token: 用户授权访问令牌，可选
            refresh_token: 用于刷新access_token的令牌，可选
            auto_refresh: 是否自动刷新token，默认为True
        """
        self.app_key = app_key
        self.secret_key = secret_key
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.auto_refresh = auto_refresh
        self.token_expire_time = 0
        self._session = None
    
    def _get_session(self):
        """获取HTTP会话，如果不存在则创建"""
        if self._session is None:
            self._session = requests.Session()
        return self._session
    
    def _check_token(self):
        """检查token是否有效，如果无效且设置了自动刷新，则刷新token"""
        if not self.access_token:
            raise ValueError("未设置access_token，请先获取授权")
        
        # 如果token即将过期且设置了自动刷新，则刷新token
        current_time = int(time.time())
        if self.token_expire_time > 0 and current_time >= self.token_expire_time - 60 and self.auto_refresh:
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
        return f"https://openapi.baidu.com/oauth/2.0/authorize?{query_string}"
    
    def get_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """通过授权码获取访问令牌
        
        Args:
            code: 授权码
            redirect_uri: 授权回调地址，必须与获取授权码时一致
            
        Returns:
            Dict: 包含access_token、refresh_token等信息的字典
        """
        session = self._get_session()
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.app_key,
            "client_secret": self.secret_key,
            "redirect_uri": redirect_uri
        }
        response = session.get("https://openapi.baidu.com/oauth/2.0/token", params=params)
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
        
        session = self._get_session()
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.app_key,
            "client_secret": self.secret_key
        }
        response = session.get("https://openapi.baidu.com/oauth/2.0/token", params=params)
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        response = session.get("https://pan.baidu.com/rest/2.0/xpan/nas?method=uinfo", params=params)
        return response.json()
    
    def get_quota(self) -> Dict[str, Any]:
        """获取用户空间配额信息
        
        Returns:
            Dict: 包含空间使用情况的字典
        """
        self._check_token()
        session = self._get_session()
        params = {"access_token": self.access_token}
        response = session.get("https://pan.baidu.com/api/quota", params=params)
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
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "dir": dir_path,
            "order": order,
            "desc": 1 if desc else 0,
            "start": start,
            "limit": limit
        }
        response = session.get("https://pan.baidu.com/rest/2.0/xpan/file?method=list", params=params)
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
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "key": keyword,
            "dir": dir_path,
            "recursion": 1 if recursive else 0
        }
        response = session.get("https://pan.baidu.com/rest/2.0/xpan/file?method=search", params=params)
        return response.json()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件信息字典
        """
        self._check_token()
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "path": file_path
        }
        response = session.get("https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas", params=params)
        return response.json()
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """创建目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            Dict: 创建结果字典
        """
        self._check_token()
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {"path": dir_path}
        response = session.post("https://pan.baidu.com/rest/2.0/xpan/file?method=create", 
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_paths)}
        response = session.post("https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=delete", 
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {
            "filelist": json.dumps([{"path": file_path, "newname": new_name}])
        }
        response = session.post("https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=rename", 
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_list)}
        response = session.post("https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=move", 
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {"filelist": json.dumps(file_list)}
        response = session.post("https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=copy", 
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
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "path": file_path
        }
        response = session.get("https://pan.baidu.com/rest/2.0/xpan/file?method=download", params=params)
        if response.status_code == 200:
            return response.json().get("dlink", "")
        return ""
    
    def download_file(self, file_path: str, local_path: str, chunk_size: int = 1024 * 1024) -> bool:
        """下载文件到本地
        
        Args:
            file_path: 云盘文件路径
            local_path: 本地保存路径
            chunk_size: 分块下载的块大小，默认1MB
            
        Returns:
            bool: 下载是否成功
        """
        download_link = self.get_download_link(file_path)
        if not download_link:
            return False
        
        session = self._get_session()
        try:
            response = session.get(download_link, stream=True)
            if response.status_code != 200:
                return False
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            # 分块下载文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            return True
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
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "path": remote_path,
            "ondup": ondup
        }
        
        with open(local_path, 'rb') as f:
            files = {'file': f}
            response = session.post(
                "https://pan.baidu.com/rest/2.0/xpan/file?method=upload",
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
        # 获取文件大小
        file_size = os.path.getsize(local_path)
        
        # 计算文件MD5
        md5 = self._calculate_file_md5(local_path)
        
        # 预创建文件
        precreate_result = self._precreate_file(remote_path, file_size, md5, ondup)
        if 'errno' in precreate_result and precreate_result['errno'] != 0:
            return precreate_result
        
        # 获取上传ID
        upload_id = precreate_result.get('uploadid', '')
        if not upload_id:
            return {"errno": -1, "errmsg": "获取上传ID失败"}
        
        # 分片上传
        block_list = []
        chunk_size = 4 * 1024 * 1024  # 4MB
        with open(local_path, 'rb') as f:
            block_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                # 上传分片
                result = self._upload_chunk(chunk, remote_path, upload_id, block_index)
                if 'errno' in result and result['errno'] != 0:
                    return result
                
                # 记录分片MD5
                block_list.append(hashlib.md5(chunk).hexdigest())
                block_index += 1
        
        # 创建文件
        return self._create_file(remote_path, file_size, upload_id, block_list, ondup)
    
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {
            "path": remote_path,
            "size": file_size,
            "isdir": 0,
            "autoinit": 1,
            "rtype": 3,  # 上传类型，3表示上传文件
            "block_list": json.dumps([]),  # 预创建时为空
            "ondup": ondup
        }
        
        response = session.post(
            "https://pan.baidu.com/rest/2.0/xpan/file?method=precreate",
            params=params,
            data=data
        )
        
        return response.json()
    
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
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "path": remote_path,
            "uploadid": upload_id,
            "partseq": block_index  # 分片索引，从0开始
        }
        
        files = {'file': chunk}
        response = session.post(
            "https://pan.baidu.com/rest/2.0/xpan/file?method=upload",
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
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {
            "path": remote_path,
            "size": file_size,
            "isdir": 0,
            "uploadid": upload_id,
            "block_list": json.dumps(block_list),
            "ondup": ondup
        }
        
        response = session.post(
            "https://pan.baidu.com/rest/2.0/xpan/file?method=create",
            params=params,
            data=data
        )
        
        return response.json()
    
    def create_share(self, file_paths: List[str], period: int = 0, 
                    password: str = None, description: str = "") -> Dict[str, Any]:
        """创建分享链接
        
        Args:
            file_paths: 要分享的文件路径列表
            period: 分享有效期，0表示永久，其他值表示有效期天数
            password: 分享密码，为None表示无密码
            description: 分享描述
            
        Returns:
            Dict: 分享结果字典
        """
        self._check_token()
        session = self._get_session()
        params = {"access_token": self.access_token}
        
        data = {
            "path_list": json.dumps(file_paths),
            "period": period,
            "channel_list": json.dumps([0]),  # 分享渠道，0表示公开分享
            "schannel": 4,  # 分享渠道，4表示网盘分享
            "description": description
        }
        
        # 如果设置了密码
        if password:
            data["pwd"] = password
        
        response = session.post(
            "https://pan.baidu.com/rest/2.0/xpan/share?method=set",
            params=params,
            data=data
        )
        
        return response.json()
    
    def list_shares(self, start: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取分享列表
        
        Args:
            start: 起始位置，用于分页
            limit: 返回条目数量，默认为100
            
        Returns:
            Dict: 包含分享列表的字典
        """
        self._check_token()
        session = self._get_session()
        params = {
            "access_token": self.access_token,
            "start": start,
            "limit": limit
        }
        
        response = session.get(
            "https://pan.baidu.com/rest/2.0/xpan/share?method=list",
            params=params
        )
        
        return response.json()
    
    def cancel_share(self, share_ids: List[str]) -> Dict[str, Any]:
        """取消分享
        
        Args:
            share_ids: 分享ID列表
            
        Returns:
            Dict: 取消分享结果字典
        """
        self._check_token()
        session = self._get_session()
        params = {"access_token": self.access_token}
        data = {"shareid_list": json.dumps(share_ids)}
        
        response = session.post(
            "https://pan.baidu.com/rest/2.0/xpan/share?method=cancel",
            params=params,
            data=data
        )
        
        return response.json()