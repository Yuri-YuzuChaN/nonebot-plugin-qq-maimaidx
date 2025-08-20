<div align='center'>
    <a><img src='https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx/master/favicon.png' width='200px' height='200px' akt='maimaidx'></a>
</div>

<div align='center'>

# nonebot-plugin-qq-maimaidx

<a href='./LICENSE'>
    <img src='https://img.shields.io/github/license/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx' alt='license'>
</a>
<img src='https://img.shields.io/badge/python-3.8+-blue.svg' alt='python'>
</div>


适用于 QQ官方BOT，可在QQ群和QQ频道使用


## 重要更新


## 安装

1. 安装 `nonebot-plugin-qq-maimaidx`

    - 使用 `nb-cli` 安装 **不可用**
        ``` python
        nb plugin install nonebot-plugin-qq-maimaidx
        ```
    - 使用 `pip` 安装 **不可用**
        ``` python
        pip install nonebot-plugin-qq-maimaidx
        ```
    - 使用源代码（不推荐） **需自行安装额外依赖**
        ``` git
        git clone https://github.com/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx
        ```
    
2. 安装 `chromium`，**相关依赖已安装，请直接使用该指令执行**

    ``` shell
    playwright install --with-deps chromium
    ```

3. 安装 `微软雅黑` 字体，解决使用 `ginfo` 指令字体不渲染的问题，例如 `ubuntu`：`apt install fonts-wqy-microhei`

## 配置
   
1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static`

   - [Cloudreve私人云盘](https://cloud.yuzuchan.moe/f/1bUn/Resource.7z)
   - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzu_yuzuchan_moe/EdGUKRSo-VpHjT2noa_9EroBdFZci-tqWjVZzKZRTEeZkw?e=a1TM40)

2. 在 `.env` 文件中配置静态文件绝对路径 `MAIMAIDXPATH`

    ``` dotenv
    MAIMAIDXPATH=path.to.static

    # 例如 windows 平台，非 "管理员模式" 运行Bot尽量避免存放在C盘
    MAIMAIDXPATH=D:\bot\static
    # 例如 linux 平台
    MAIMAIDXPATH=/root/static
    ```

3. 可选，如果拥有 `diving-fish 查分器` 的开发者 `Token`，请在 `.env` 文件中配置 `MAIMAIDXTOKEN`
   
    ``` dotenv
    MAIMAIDXTOKEN=MAIMAITOKEN
    ```

4. 可选，如果你的服务器或主机不能顺利流畅的访问查分器和别名库的API，请在 `.env` 文件中配置代理。均为香港服务器代理中转，例如你的服务器访问查分器很困难，请设置 `MAIMAIDXPROBERPROXY` 为 `true`，别名库同理

    ``` dotenv
    # 查分器代理，推荐境外服务器使用
    MAIMAIDXPROBERPROXY=false
    # 别名代理，推荐国内服务器使用
    MAIMAIDXALIASPROXY=false
    ```

## 指令

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-qq-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)
