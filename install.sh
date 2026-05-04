#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/bilibili-downloader"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ">>> 安装 Bilibili 下载器..."

# 复制应用文件
mkdir -p "$APP_DIR"
cp -r main.py requirements.txt static "$APP_DIR/"

# 创建虚拟环境并安装依赖
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

# 创建启动脚本
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/bilibili-dl" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
"$APP_DIR/venv/bin/uvicorn" main:app --host 127.0.0.1 --port 8963 &
sleep 1.5
xdg-open http://localhost:8963
wait
EOF
chmod +x "$BIN_DIR/bilibili-dl"

# 创建桌面快捷方式
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/bilibili-downloader.desktop" <<EOF
[Desktop Entry]
Name=Bilibili 下载器
Comment=下载 Bilibili 视频
Exec=$BIN_DIR/bilibili-dl
Icon=video-x-generic
Terminal=false
Type=Application
Categories=Network;Video;
EOF

echo ">>> 安装完成！"
echo "    命令行启动: bilibili-dl"
echo "    或在应用菜单中搜索 'Bilibili 下载器'"
echo ""
echo "    提示: 确保 $BIN_DIR 在 PATH 中"
echo "    如未生效，执行: export PATH=\"\$HOME/.local/bin:\$PATH\""
