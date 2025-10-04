"""
Config Manager - 設定管理システム

config.iniファイルの読み書きと設定管理を行う
"""

import os
import configparser
from typing import Any, Optional
from pathlib import Path


class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_path: Optional[str] = None):
        """
        設定管理の初期化

        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if config_path is None:
            # プロジェクトルートのdata/config.iniを使用
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "data" / "config.ini"

        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        """設定ファイルの読み込み"""
        try:
            if self.config_path.exists():
                self.config.read(self.config_path, encoding='utf-8')
                print(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                print(f"設定ファイルが見つかりません: {self.config_path}")
                print("デフォルト設定を使用します")
                self._create_default_config()
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """デフォルト設定の作成"""
        self.config['Application'] = {
            'version': '1.0.0',
            'auto_start': 'true',
            'minimize_to_tray': 'true'
        }

        self.config['Hotkey'] = {
            'double_copy_interval': '0.5',
            'enable_global_hotkey': 'true'
        }

        self.config['Translation'] = {
            'default_target_language': 'ja',
            'default_source_language': 'auto',
            'auto_detect_language': 'true',
            'timeout_duration': '3.0'
        }

        self.config['UI'] = {
            'window_width': '500',
            'window_height': '700',
            'split_ratio': '0.5',
            'theme': 'system',
            'font_family': 'Noto Sans JP'
        }

        self.config['SystemTray'] = {
            'show_tray_icon': 'true',
            'tooltip': 'CCTranslation - Translation Utility',
            'icon_path': 'icon/CCT_icon.ico'
        }

        self.config['Advanced'] = {
            'enable_logging': 'true',
            'log_level': 'INFO',
            'max_history_count': '100'
        }

    def save_config(self) -> None:
        """設定ファイルの保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print(f"設定ファイルを保存しました: {self.config_path}")
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        設定値の取得

        Args:
            section: セクション名
            key: キー名
            fallback: デフォルト値

        Returns:
            設定値
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """整数設定値の取得"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """ブール値設定値の取得"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """浮動小数点設定値の取得"""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """真偽値設定値の取得"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def set(self, section: str, key: str, value: Any) -> None:
        """
        設定値の設定

        Args:
            section: セクション名
            key: キー名
            value: 設定値
        """
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, key, str(value))

    # アプリケーション設定
    def get_version(self) -> str:
        """アプリケーションバージョンの取得"""
        return self.get('Application', 'version', '1.0.0')

    def is_auto_start(self) -> bool:
        """自動起動設定の取得"""
        return self.get_bool('Application', 'auto_start', True)

    def is_minimize_to_tray(self) -> bool:
        """トレイへの最小化設定の取得"""
        return self.get_bool('Application', 'minimize_to_tray', True)

    # ホットキー設定
    def get_double_copy_interval(self) -> float:
        """ダブルコピー検出間隔の取得"""
        return self.get_float('Hotkey', 'double_copy_interval', 0.5)

    def is_global_hotkey_enabled(self) -> bool:
        """グローバルホットキー有効設定の取得"""
        return self.get_bool('Hotkey', 'enable_global_hotkey', True)

    # 翻訳設定
    def get_default_target_language(self) -> str:
        """デフォルト翻訳先言語の取得"""
        return self.get('Translation', 'default_target_language', 'ja')

    def get_default_source_language(self) -> str:
        """デフォルト翻訳元言語の取得"""
        return self.get('Translation', 'default_source_language', 'auto')

    def is_auto_detect_language(self) -> bool:
        """自動言語検出設定の取得"""
        return self.get_bool('Translation', 'auto_detect_language', True)

    def get_timeout_duration(self) -> float:
        """タイムアウト時間の取得"""
        return self.get_float('Translation', 'timeout_duration', 3.0)

    # UI設定
    def get_window_width(self) -> int:
        """ウィンドウ幅の取得"""
        return self.get_int('UI', 'window_width', 500)

    def get_window_height(self) -> int:
        """ウィンドウ高さの取得"""
        return self.get_int('UI', 'window_height', 700)

    def get_split_ratio(self) -> float:
        """分割比率の取得"""
        return self.get_float('UI', 'split_ratio', 0.5)

    def get_theme(self) -> str:
        """テーマ設定の取得"""
        return self.get('UI', 'theme', 'system')

    def get_font_family(self) -> str:
        """フォントファミリーの取得"""
        return self.get('UI', 'font_family', 'Noto Sans JP')

    # システムトレイ設定
    def is_tray_icon_enabled(self) -> bool:
        """システムトレイアイコン有効設定の取得"""
        return self.get_bool('SystemTray', 'show_tray_icon', True)

    def get_tray_tooltip(self) -> str:
        """システムトレイツールチップの取得"""
        return self.get('SystemTray', 'tooltip', 'CCTranslation - Translation Utility')

    def get_icon_path(self) -> str:
        """アイコンパスの取得"""
        return self.get('SystemTray', 'icon_path', 'icon/CCT_icon.ico')

    # 高度設定
    def is_logging_enabled(self) -> bool:
        """ログ機能有効設定の取得"""
        return self.get_bool('Advanced', 'enable_logging', True)

    def get_log_level(self) -> str:
        """ログレベルの取得"""
        return self.get('Advanced', 'log_level', 'INFO')

    def get_max_history_count(self) -> int:
        """最大履歴数の取得"""
        return self.get_int('Advanced', 'max_history_count', 100)

    # 設定値の更新メソッド
    def set_default_target_language(self, language: str) -> None:
        """デフォルト翻訳先言語の設定"""
        self.set('Translation', 'default_target_language', language)

    def set_window_size(self, width: int, height: int) -> None:
        """ウィンドウサイズの設定"""
        self.set('UI', 'window_width', width)
        self.set('UI', 'window_height', height)

    def set_split_ratio(self, ratio: float) -> None:
        """分割比率の設定"""
        self.set('UI', 'split_ratio', ratio)


# テスト用
if __name__ == "__main__":
    config = ConfigManager()

    print("=== 設定テスト ===")
    print(f"バージョン: {config.get_version()}")
    print(f"翻訳先言語: {config.get_default_target_language()}")
    print(f"ウィンドウサイズ: {config.get_window_width()}x{config.get_window_height()}")
    print(f"分割比率: {config.get_split_ratio()}")
    print(f"タイムアウト時間: {config.get_timeout_duration()}秒")

    # 設定変更テスト
    config.set_default_target_language('en')
    config.save_config()
    print(f"翻訳先言語を変更: {config.get_default_target_language()}")
