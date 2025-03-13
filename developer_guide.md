# 1. 开发指南

## 1.1 环境设置

1. 克隆仓库：
```bash
git clone https://github.com/guyue55/py_example.git
cd py_example
```

2. 安装开发依赖：
```bash
pip install -e .
```

## 2.2 运行测试

```bash
python -m unittest discover tests
```

## 2.3 代码贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 运行测试确保通过
5. 提交 Pull Request

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