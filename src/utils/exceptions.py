"""
Custom Exceptions - カスタム例外クラス

CCTranslation専用の例外定義
"""


class CCTranslationException(Exception):
    """CCTranslation基底例外クラス"""
    pass


class TranslationError(CCTranslationException):
    """翻訳エラー"""
    pass


class TranslationTimeoutError(CCTranslationException):
    """翻訳タイムアウトエラー"""
    pass


class ClipboardError(CCTranslationException):
    """クリップボードエラー"""
    pass


class HotkeyError(CCTranslationException):
    """ホットキーエラー"""
    pass


class ConfigError(CCTranslationException):
    """設定エラー"""
    pass


class NetworkError(CCTranslationException):
    """ネットワークエラー"""
    pass


class JapaneseKeyboardError(CCTranslationException):
    """日本語キーボード特殊キーエラー"""
    pass
