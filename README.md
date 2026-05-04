# Bilibili 下载器

基于 yt-dlp + FastAPI 的 Bilibili 视频下载工具，支持选择分辨率、合集批量下载。

## 功能

- 输入视频或合集链接，自动识别系列剧集
- 选择下载分辨率（360p ~ 1080p+）
- 合集支持勾选部分集数下载
- 自定义保存路径
- 下载中心实时显示进度，完成后提示保存位置
- 支持读取浏览器 Cookie（用于高清画质或登录限制内容）

## 系统要求

- Linux
- Python 3.10+
- ffmpeg（用于合并视频音频）

```bash
# Arch Linux
sudo pacman -S python ffmpeg

# Ubuntu/Debian
sudo apt install python3 python3-venv ffmpeg
```

## 安装

```bash
git clone <repo-url>
cd videoCapture
chmod +x install.sh
./install.sh
```

安装后通过命令行或应用菜单启动：

```bash
bilibili-dl
```

浏览器会自动打开 `http://localhost:8963`。

## 开发模式运行

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/uvicorn main:app --reload --port 8000
```

## 卸载

```bash
./uninstall.sh
```

## Cookie 说明

下载高清视频（1080p+）或登录限制内容时，在页面选择已登录 Bilibili 的浏览器（Chrome / Firefox 等），工具会自动读取本地 Cookie。
