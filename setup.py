from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sdk_utils",
    version="0.1.2",
    author="Guyue",
    author_email="guyuecw@qq.com",
    description="一个集成SDK的工具库，如百度云盘API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guyue55/sdk_utils",
    packages=find_packages(),
    license="MIT",
    license_files="LICENSE",
    install_requires=[
        "requests>=2.25.0",
        "bypy>=1.7.0",
        "tqdm>=4.50.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.6",
    keywords="baidu, cloud, sdk, api, client",
)