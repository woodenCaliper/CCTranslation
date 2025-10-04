# CCTranslation 設計仕様書

## プロジェクト概要
- **プロジェクト名**: CCTranslation
- **設計方式**: KIRO式設計
- **作成日**: 2024年
- **バージョン**: 1.0

## 1. システムアーキテクチャ

### 1.1 全体アーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                    CCTranslation Application                │
├─────────────────────────────────────────────────────────────┤
│  Presentation Layer (UI Layer)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Main Window   │  │  Settings UI    │  │ System Tray │  │
│  │   (tkinter)     │  │   (tkinter)     │  │  (pystray)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Application Layer (Business Logic)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Translation    │  │   Clipboard     │  │   Hotkey    │  │
│  │   Manager       │  │    Manager      │  │  Manager    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Config        │  │   History       │  │  Language   │  │
│  │   Manager       │  │    Manager      │  │  Manager    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  External Services                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Google Translate│  │  Windows API    │  │   File      │  │
│  │     API         │  │  (pyWinhook)    │  │  System     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 モジュール構成
```
CCTranslation/
├── src/
│   ├── main.py                 # アプリケーションエントリーポイント
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # メインウィンドウ
│   │   ├── settings_window.py  # 設定ウィンドウ
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── text_area.py    # テキストエリアコンポーネント
│   │       ├── language_selector.py  # 言語選択コンポーネント
│   │       └── split_pane.py   # 分割パネルコンポーネント
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app.py             # アプリケーションコントローラー
│   │   ├── translation.py     # 翻訳処理
│   │   ├── clipboard.py       # クリップボード処理
│   │   ├── hotkey.py          # ホットキー監視
│   │   └── system_tray.py     # システムトレイ管理
│   ├── data/
│   │   ├── __init__.py
│   │   ├── config.py          # 設定管理
│   │   ├── history.py         # 履歴管理
│   │   └── language.py        # 言語データ管理
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # ログ管理
│       ├── exceptions.py      # カスタム例外
│       └── helpers.py         # ユーティリティ関数
├── icon/
│   └── CCT_icon.ico           # システムトレイアイコン
├── data/
│   ├── config.ini             # 設定ファイル
│   ├── history.json           # 翻訳履歴
│   └── languages.json         # 言語データ
├── requirements.txt           # 依存関係
└── README.md                  # プロジェクト説明
```

## 2. クラス設計

### 2.1 メインアプリケーションクラス
```python
class CCTranslationApp:
    """CCTranslationメインアプリケーションクラス"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        self.language_manager = LanguageManager()
        self.translation_manager = TranslationManager()
        self.clipboard_manager = ClipboardManager()
        self.hotkey_manager = HotkeyManager()
        self.system_tray = SystemTrayManager()
        self.main_window = None
        self.settings_window = None
    
    def run(self):
        """アプリケーション実行"""
        pass
    
    def shutdown(self):
        """アプリケーション終了"""
        pass
```

### 2.2 翻訳管理クラス
```python
class TranslationManager:
    """翻訳処理を管理するクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.translator = GoogleTranslator()
        self.timeout_duration = 3.0  # 3秒タイムアウト
    
    def translate_with_timeout(self, text: str, target_lang: str, 
                             source_lang: str = 'auto', 
                             progress_callback=None) -> TranslationResult:
        """タイムアウト付きでテキストを翻訳する"""
        pass
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> TranslationResult:
        """テキストを翻訳する"""
        pass
    
    def detect_language(self, text: str) -> str:
        """言語を自動検出する"""
        pass
    
    def _execute_translation_async(self, text: str, target_lang: str, 
                                 source_lang: str, progress_callback):
        """非同期翻訳実行"""
        pass
```

### 2.3 クリップボード管理クラス
```python
class ClipboardManager:
    """クリップボード処理を管理するクラス"""
    
    def __init__(self):
        self.last_content = ""
        self.last_timestamp = 0
    
    def get_clipboard_content(self) -> str:
        """クリップボードの内容を取得"""
        pass
    
    def set_clipboard_content(self, content: str) -> None:
        """クリップボードに内容を設定"""
        pass
    
    def has_changed(self) -> bool:
        """クリップボード内容が変更されたかチェック"""
        pass
```

### 2.4 ホットキー管理クラス
```python
class HotkeyManager:
    """ホットキー監視を管理するクラス"""
    
    def __init__(self, callback_func):
        self.callback = callback_func
        self.hook = None
        self.double_copy_detector = DoubleCopyDetector()
        # 日本語キーボード特殊キーの除外リスト
        self.excluded_keys = {
            'VK_KANJI',      # 全角半角キー
            'VK_CONVERT',    # 変換キー
            'VK_NONCONVERT', # 無変換キー
            'VK_KANA',       # カタカナひらがなキー
        }
    
    def start_monitoring(self) -> None:
        """ホットキー監視を開始"""
        pass
    
    def stop_monitoring(self) -> None:
        """ホットキー監視を停止"""
        pass
    
    def _keyboard_hook(self, event) -> None:
        """キーボードイベント処理（日本語キーボード対応）"""
        # 特殊キーの除外処理
        if self._is_excluded_key(event):
            return True  # イベントをそのまま通す
        
        # Ctrl+C のみを処理
        if self._is_ctrl_c_combination(event):
            self._handle_ctrl_c(event)
        
        return True  # イベントをそのまま通す
    
    def _is_excluded_key(self, event) -> bool:
        """除外すべき特殊キーかチェック"""
        pass
    
    def _is_ctrl_c_combination(self, event) -> bool:
        """Ctrl+C の組み合わせかチェック"""
        pass
    
    def _handle_ctrl_c(self, event) -> None:
        """Ctrl+C の処理"""
        pass
```

## 3. データフロー・処理フロー

### 3.1 翻訳処理フロー
```
ユーザー操作 (Ctrl+C連続押下)
    ↓
ホットキー検出 (pyWinhook)
    ↓
クリップボード内容取得 (pyperclip)
    ↓
内容変更チェック
    ↓
タイムアウト監視開始 (3秒タイマー)
    ↓
並行処理:
    ├─ 言語自動検出 (googletrans)
    ├─ 翻訳実行 (googletrans)
    └─ 3秒タイマー監視
    ↓
分岐処理:
    ├─ 3秒以内完了 → 翻訳結果表示
    └─ 3秒経過 → ステータス表示ウィンドウ表示
    ↓
翻訳完了時に結果更新
    ↓
履歴保存 (JSON)
```

### 3.1.1 タイムアウト処理詳細
```
3秒経過時の動作:
    ↓
ステータスウィンドウ表示
    ├─ 翻訳中... (進行中の場合)
    ├─ ネットワーク接続中... (接続試行中の場合)
    └─ 翻訳失敗 (エラー発生時)
    ↓
翻訳完了時の動作:
    ├─ 成功 → ステータスウィンドウを通常の翻訳結果表示に切り替え
    │   ├─ 原文エリアに翻訳前テキスト表示
    │   ├─ 翻訳文エリアに翻訳後テキスト表示
    │   ├─ 言語情報の表示
    │   └─ コピーボタンの有効化
    └─ 失敗 → エラーメッセージ表示（ステータスウィンドウ内）
```

### 3.2 UI更新フロー
```
翻訳完了イベント
    ↓
UIスレッドに通知
    ↓
メインウィンドウ更新
    ├─ 原文エリア更新
    ├─ 翻訳文エリア更新
    └─ 言語情報更新
    ↓
ウィンドウ表示・最前面化
```

### 3.3 設定管理フロー
```
設定変更イベント
    ↓
ConfigManager更新
    ↓
設定ファイル保存 (config.ini)
    ↓
関連コンポーネント通知
    ├─ ホットキー設定更新
    ├─ 言語設定更新
    └─ UI設定更新
```

## 4. UI/UXコンポーネント設計

### 4.1 メインウィンドウコンポーネント
```python
class MainWindow:
    """メインウィンドウクラス"""
    
    def __init__(self, app: CCTranslationApp):
        self.app = app
        self.root = tk.Tk()
        self.status_frame = None  # ステータス表示フレーム
        self.setup_ui()
    
    def setup_ui(self):
        """UIコンポーネントのセットアップ"""
        # ウィンドウ設定
        # 言語選択コンポーネント
        # 分割パネルコンポーネント
        # テキストエリアコンポーネント
        # ステータス表示フレーム
        # コピーボタン
        pass
    
    def update_translation(self, result: TranslationResult):
        """翻訳結果の表示更新"""
        pass
    
    def show_status_window(self):
        """3秒タイムアウト時のステータスウィンドウ表示"""
        pass
    
    def update_status(self, status: str, message: str = ""):
        """ステータス表示更新"""
        # status: "translating", "connecting", "error"
        # message: 詳細メッセージ
        pass
    
    def switch_to_translation_display(self, result: TranslationResult):
        """ステータス表示から通常の翻訳結果表示に切り替え"""
        # ステータスウィンドウの内容を翻訳結果表示に変更
        # 原文エリア、翻訳文エリア、言語情報、コピーボタンを表示
        pass
    
    def hide_status(self):
        """ステータス表示を非表示"""
        pass
```

### 4.2 テキストエリアコンポーネント
```python
class TextArea:
    """テキストエリアコンポーネント"""
    
    def __init__(self, parent, title: str, readonly: bool = True):
        self.parent = parent
        self.title = title
        self.readonly = readonly
        self.setup_component()
    
    def setup_component(self):
        """コンポーネントのセットアップ"""
        # ラベル
        # ScrolledText
        # フォント設定
        # 自動サイズ調整
        pass
    
    def set_text(self, text: str):
        """テキスト設定"""
        pass
    
    def get_text(self) -> str:
        """テキスト取得"""
        pass
    
    def auto_resize(self):
        """自動サイズ調整"""
        pass
```

### 4.3 分割パネルコンポーネント
```python
class SplitPane:
    """分割パネルコンポーネント"""
    
    def __init__(self, parent, orientation='vertical'):
        self.parent = parent
        self.orientation = orientation
        self.paned_window = None
        self.setup_component()
    
    def setup_component(self):
        """コンポーネントのセットアップ"""
        # PanedWindow作成
        # ドラッグ可能設定
        # 最小サイズ設定
        pass
    
    def add_pane(self, widget, weight: int = 1):
        """パネル追加"""
        pass
```

## 5. 設定・データ管理設計

### 5.1 設定ファイル構造 (config.ini)
```ini
[Application]
version = 1.0.0
auto_start = true
minimize_to_tray = true

[Hotkey]
double_copy_interval = 0.5
enable_global_hotkey = true

[Translation]
default_target_language = ja
default_source_language = auto
auto_detect_language = true

[UI]
window_width = 500
window_height = 700
split_ratio = 0.5
theme = system

[SystemTray]
show_tray_icon = true
tooltip = CCTranslation - 翻訳ユーティリティ
```

### 5.2 履歴ファイル構造 (history.json)
```json
{
  "version": "1.0.0",
  "history": [
    {
      "id": "uuid-string",
      "timestamp": "2024-01-01T12:00:00Z",
      "source_text": "Hello, how are you?",
      "target_text": "こんにちは、お元気ですか？",
      "source_language": "en",
      "target_language": "ja",
      "detected_language": "en"
    }
  ]
}
```

### 5.3 言語データ構造 (languages.json)
```json
{
  "languages": {
    "auto": "自動検出",
    "ja": "日本語",
    "en": "英語",
    "zh": "中国語",
    "ko": "韓国語",
    "es": "スペイン語",
    "fr": "フランス語",
    "de": "ドイツ語"
  }
}
```

## 6. エラーハンドリング・例外処理設計

### 6.1 カスタム例外クラス
```python
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
```

### 6.2 ステータス管理クラス
```python
class TranslationStatus:
    """翻訳ステータス管理クラス"""
    
    IDLE = "idle"
    DETECTING_LANGUAGE = "detecting_language"
    TRANSLATING = "translating"
    CONNECTING = "connecting"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    
    def __init__(self):
        self.current_status = self.IDLE
        self.message = ""
        self.start_time = None
        self.timeout_duration = 3.0
    
    def set_status(self, status: str, message: str = ""):
        """ステータス設定"""
        pass
    
    def is_timeout(self) -> bool:
        """タイムアウト判定"""
        pass
    
    def get_elapsed_time(self) -> float:
        """経過時間取得"""
        pass
```

### 6.3 エラーハンドリング戦略
- **翻訳エラー**: ユーザーにエラーメッセージ表示、再試行オプション提供
- **ネットワークエラー**: 接続状態確認、リトライ機能
- **ファイルエラー**: デフォルト設定への復帰
- **ホットキーエラー**: 代替操作の提供
- **タイムアウトエラー**: 3秒経過時にステータスウィンドウ表示、進行状況の可視化
- **日本語キーボード特殊キーエラー**: 全角半角キー等の特殊キーによるアプリ停止を防止

### 6.4 タイムアウト処理戦略
- **3秒以内完了**: 翻訳結果を直接表示
- **3秒経過**: ステータスウィンドウを表示し、以下の情報を提供
  - 翻訳中... (言語検出・翻訳処理中)
  - ネットワーク接続中... (API接続試行中)
  - 翻訳失敗 (エラー発生時)
- **翻訳完了時**: 
  - **成功**: ステータスウィンドウを通常の翻訳結果表示に切り替え
    - 原文エリア、翻訳文エリア、言語情報、コピーボタンを表示
    - ユーザーは通常通り翻訳結果を確認・操作可能
  - **失敗**: エラーメッセージをステータスウィンドウ内に表示
- **ユーザビリティ**: アプリの動作状況を常にユーザーに提供し、最終的に通常の翻訳結果を表示

### 6.5 日本語キーボード対応戦略
**重要**: 日本語キーボードの全角半角キー等の特殊キーによるアプリ停止を防止

#### 6.5.1 除外すべき特殊キー
- **VK_KANJI**: 全角半角キー（最優先で除外）
- **VK_CONVERT**: 変換キー
- **VK_NONCONVERT**: 無変換キー
- **VK_KANA**: カタカナひらがなキー

#### 6.5.2 実装方針
- **pyWinhook使用**: keyboardライブラリではなくpyWinhookで安全な処理
- **イベントフィルタリング**: 特殊キーイベントを完全に除外
- **Ctrl+C専用**: Ctrl+Cの組み合わせのみを監視対象とする
- **イベントパススルー**: 除外キーはシステムにそのまま通す

#### 6.5.3 テスト要件
- 全角半角キー押下時のアプリ停止テスト
- 変換/無変換キー押下時の動作確認
- カタカナひらがなキー押下時の動作確認
- Ctrl+C以外のキー組み合わせでの誤動作確認

---

**更新履歴**
- 2024-XX-XX: 初版作成
