# SDK Utils

一个用于SDK开发的工具库，提供构建Python SDK的通用功能。目前主要封装了百度云盘的常用操作，使开发者能够轻松地在自己的应用中集成百度云盘功能。

## 安装方法

```bash
pip install sdk_utils
```

## 主要功能

- 百度云盘API客户端
  - 文件上传、下载、分享、移动、复制、删除等基本功能
  - 目录操作、文件搜索和大文件分片上传等高级功能
  - OAuth2.0授权认证流程
- API客户端工具
  - 认证辅助工具
  - 速率限制和重试机制
  - 响应解析和错误处理
  - 日志记录和调试工具

## 使用示例

### 百度云盘客户端

```python
from sdk_utils.baidu_cloud import BaiduCloudClient

# 创建百度云盘客户端
client = BaiduCloudClient(
    app_key="your_app_key",
    secret_key="your_secret_key",
    access_token="your_access_token",  # 可选，如果已有token
    refresh_token="your_refresh_token"  # 可选，用于自动刷新token
)

# 获取授权URL（如果没有access_token）
auth_url = client.get_auth_url(redirect_uri="http://localhost:8000/callback")
print(f"请访问此URL进行授权: {auth_url}")

# 通过授权码获取token
token_info = client.get_access_token(code="authorization_code", redirect_uri="http://localhost:8000/callback")

# 上传文件
result = client.upload_file(local_path="/path/to/local/file.txt", remote_path="/apps/your_app/file.txt")

# 下载文件
client.download_file(remote_path="/apps/your_app/file.txt", local_path="/path/to/save/file.txt")

# 获取文件列表
file_list = client.list_files(dir_path="/apps/your_app")
for file in file_list:
    print(f"文件名: {file['server_filename']}, 大小: {file['size']}")
```

### 使用bypy封装的百度云盘工具

```python
from sdk_utils.baidu_cloud_bypy import BaiduPanTools

# 创建工具实例（首次使用会自动进行授权）
pan = BaiduPanTools()

# 上传文件
pan.upload_file("test_upload.txt")

# 下载文件
pan.download_file("test_upload.txt", "downloads")

# 查看文件列表
file_list = pan.list_files()
print(file_list)

# 同步整个文件夹
pan.sync_folder("local_folder", "remote_folder")
```

## 文档

完整文档请访问[我们的文档站点](https://github.com/guyue55/sdk_utils)。

### 开发文档

如果您想参与开发，请查看[开发者指南](./developer_guide.md)了解更多信息。

## 贡献

欢迎贡献代码！请随时提交Pull Request。

贡献步骤：
1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 运行测试确保通过
5. 提交 Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](./LICENSE)文件。