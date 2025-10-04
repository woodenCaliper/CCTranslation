"""
Hotkey Manager - ホットキー監視システム

pynputを使用した日本語キーボード対応のホットキー監視
"""

# pynput実装を正式版として使用
from .hotkey_pynput import PynputHotkeyManager as HotkeyManager