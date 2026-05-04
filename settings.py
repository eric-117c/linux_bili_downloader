import json
from pathlib import Path


class Settings:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "bilibili-downloader"
        self.config_file = self.config_dir / "settings.json"
        self.defaults = {
            "download_path": str(Path.home() / "Downloads" / "bilibili"),
            "browser": "不使用Cookie",
            "speed_limit": "",  # 空表示不限速，格式如 "5M"
            "default_resolution": "1080",
            "auto_start_download": False,
            "theme": "dark",
        }
        self.data = self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return {**self.defaults, **json.load(f)}
            except:
                pass
        return self.defaults.copy()

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
