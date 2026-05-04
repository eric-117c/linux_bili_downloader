#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/bilibili-downloader"

rm -rf "$APP_DIR"
rm -f "$HOME/.local/bin/bilibili-dl"
rm -f "$HOME/.local/share/applications/bilibili-downloader.desktop"

echo ">>> 已卸载 Bilibili 下载器"
