# 开发者指南

## 1. 环境设置

### 1.1 开发环境准备

1. 克隆仓库：
```bash
git clone https://github.com/guyue55/py_sdk_utils.git
cd py_sdk_utils
```

2. 安装开发依赖：
```bash
pip install -e .
```

### 1.2 开发工具推荐

- 编辑器：VS Code、PyCharm
- 代码风格检查：flake8、pylint
- 代码格式化：black、isort
- 测试工具：pytest

## 2. 开发流程

### 2.1 代码规范

- 遵循PEP 8编码规范
- 使用类型注解（Python 3.6+）
- 为所有公共API编写文档字符串
- 保持代码简洁，遵循SOLID原则

### 2.2 运行测试

```bash
python -m unittest discover tests
```

或者使用pytest：

```bash
python -m pytest tests/
```

### 2.3 代码贡献指南

1. Fork 项目仓库
2. 创建功能分支（feature/xxx 或 bugfix/xxx）
3. 编写代码和测试
4. 提交变更（使用规范的提交信息）
5. 运行测试确保通过
6. 提交 Pull Request

#### 提交信息规范

提交信息应当遵循以下格式：

```
<类型>: <简短描述>

<详细描述>
```

类型可以是：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码风格修改（不影响代码运行的变动）
- refactor: 代码重构（既不是新增功能，也不是修改bug的代码变动）
- test: 增加测试
- chore: 构建过程或辅助工具的变动

# 3. 发布流程

## 3.1 版本管理

- 遵循语义化版本规范
- 在 setup.py 中更新版本号
- 添加版本更新日志

## 3.2 打包和发布

先安装依赖
```bash
python -m pip install --upgrade setuptools wheel twine
```

1. 构建分发包：
```bash
python setup.py sdist bdist_wheel
```

2. 检查包是否符合PyPI的要求
```bash
python -m twine check dist/*
```

3. 上传到 **PyPI**：
```bash
python -m twine upload dist/*
```


**注意事项**

- **API token**：上传到**PyPI**需要API token，没有的话先去网站注册账号再生成API token（ https://pypi.org/）
- **避免每次都要输入token**：设置$HOME/.pypirc
    ```
    [pypi]
    username = __token__
    password = pypi-xxxxxx
    ```