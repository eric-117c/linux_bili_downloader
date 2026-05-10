#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/bilibili-downloader"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ">>> 安装 Bilibili 下载器..."

# 检查源文件
for f in app.py settings.py settings_dialog.py requirements.txt; do
    if [ ! -f "$f" ]; then
        echo "错误: 找不到 $f，请在项目根目录下运行此脚本" >&2
        exit 1
    fi
done

# ── 检测发行版 ──────────────────────────────────────────────────────────────
detect_distro() {
    if command -v pacman &>/dev/null; then echo "arch"
    elif command -v apt-get &>/dev/null; then echo "debian"
    elif command -v dnf &>/dev/null; then echo "fedora"
    elif command -v zypper &>/dev/null; then echo "suse"
    else echo "unknown"
    fi
}

install_pkg() {
    local pkg_arch="$1" pkg_deb="$2" pkg_rpm="$3" pkg_suse="$4"
    local distro; distro=$(detect_distro)
    case "$distro" in
        arch)   sudo pacman -S --noconfirm "$pkg_arch" ;;
        debian) sudo apt-get install -y "$pkg_deb" ;;
        fedora) sudo dnf install -y "$pkg_rpm" ;;
        suse)   sudo zypper install -y "$pkg_suse" ;;
        *)
            echo "  无法自动安装，请手动安装后重试" >&2
            return 1
            ;;
    esac
}

# ── Python 3 ────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo ">>> 未检测到 Python 3，尝试安装..."
    install_pkg python python3 python3 python3
else
    pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo ">>> Python $pyver 已就绪"
fi

# ── python3-venv（Debian/Ubuntu 单独打包）────────────────────────────────────
if ! python3 -c "import venv" &>/dev/null; then
    echo ">>> 未检测到 python3-venv，尝试安装..."
    distro=$(detect_distro)
    if [ "$distro" = "debian" ]; then
        sudo apt-get install -y python3-venv python3-full
    fi
fi

# ── ffmpeg ──────────────────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo ">>> 未检测到 ffmpeg，尝试安装..."
    install_pkg ffmpeg ffmpeg ffmpeg ffmpeg
    if ! command -v ffmpeg &>/dev/null; then
        echo "警告: ffmpeg 安装失败，视频合并功能将不可用" >&2
    fi
else
    echo ">>> ffmpeg 已就绪"
fi

# 复制应用文件
mkdir -p "$APP_DIR"
cp app.py settings.py settings_dialog.py requirements.txt "$APP_DIR/"

# 创建虚拟环境并安装依赖
if [ ! -f "$APP_DIR/venv/bin/python" ]; then
    python3 -m venv "$APP_DIR/venv"
fi

if ! "$APP_DIR/venv/bin/python" -c "import PyQt6, yt_dlp" &>/dev/null; then
    echo ">>> 安装依赖（PyQt6 较大，请耐心等待）..."
    "$APP_DIR/venv/bin/pip" install --upgrade pip
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
else
    echo ">>> 依赖已安装，跳过"
fi

# 创建启动脚本
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/bilibili-dl" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
"$APP_DIR/venv/bin/python" app.py
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

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ">>> 安装完成！"
echo "    命令行启动: bilibili-dl"
echo "    或在应用菜单中搜索 'Bilibili 下载器'"
echo ""
echo "    提示: 确保 $BIN_DIR 在 PATH 中"
echo "    如未生效，执行: export PATH=\"\$HOME/.local/bin:\$PATH\""
