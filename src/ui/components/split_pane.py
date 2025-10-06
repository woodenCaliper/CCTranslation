"""
Split Pane Component - 分割パネルコンポーネント

ドラッグ可能な分割バーを持つパネルコンポーネント
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable


class SplitPane:
    """分割パネルコンポーネント"""

    def __init__(self, parent, orientation='vertical'):
        """
        初期化

        Args:
            parent: 親ウィジェット
            orientation: 分割方向 ('vertical' または 'horizontal')
        """
        self.parent = parent
        self.orientation = orientation
        self.paned_window: Optional[ttk.PanedWindow] = None
        self.panes: List[tk.Widget] = []
        self.weights: List[int] = []
        self.min_sizes: List[int] = []

        self.setup_component()

    def setup_component(self):
        """コンポーネントのセットアップ"""
        # PanedWindow作成
        self.paned_window = ttk.PanedWindow(
            self.parent,
            orient=self.orientation
        )
        print(f"[DEBUG] PanedWindow作成完了: orientation={self.orientation}")

        # スタイル設定
        self._configure_style()
        print(f"[DEBUG] スタイル設定完了")

    def _configure_style(self):
        """スタイル設定"""
        style = ttk.Style()

        # 分割バーのスタイルを明示的に設定
        sash_width = 8
        sash_relief = 'raised'
        sash_pad = 2

        if self.orientation == 'vertical':
            # 垂直分割の場合
            style_name = "Vertical.TPanedwindow"
            style.configure(style_name,
                          sashwidth=sash_width,
                          sashrelief=sash_relief,
                          sashpad=sash_pad)
            self.paned_window.configure(style=style_name)
            print(f"[DEBUG] 垂直分割スタイル設定: sashwidth={sash_width}, sashrelief={sash_relief}")
        else:
            # 水平分割の場合
            style_name = "Horizontal.TPanedwindow"
            style.configure(style_name,
                          sashwidth=sash_width,
                          sashrelief=sash_relief,
                          sashpad=sash_pad)
            self.paned_window.configure(style=style_name)
            print(f"[DEBUG] 水平分割スタイル設定: sashwidth={sash_width}, sashrelief={sash_relief}")

        # 分割バーが表示されることを確認
        try:
            actual_sash_width = style.lookup('TPanedwindow', 'sashwidth')
            print(f"[DEBUG] 実際の分割バー幅: {actual_sash_width}")
        except Exception as e:
            print(f"[DEBUG] 分割バー幅確認エラー: {e}")

    def add_pane(self, widget: tk.Widget, weight: int = 1, min_size: int = 50):
        """
        パネル追加

        Args:
            widget: 追加するウィジェット
            weight: 重み（リサイズ時の比率）
            min_size: 最小サイズ
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        print(f"[DEBUG] パネル追加開始: {widget}, 最小サイズ: {min_size}")

        # パネルを追加
        self.paned_window.add(widget)
        print(f"[DEBUG] パネル追加完了: {widget}")

        # 情報を保存
        self.panes.append(widget)
        self.weights.append(weight)
        self.min_sizes.append(min_size)

        # 最小サイズ設定はttk.PanedWindowではサポートされていないためスキップ
        print(f"[DEBUG] 最小サイズ設定スキップ: {min_size} (ttk.PanedWindowでは非サポート)")

        # 分割バーの状態を確認
        try:
            sash_count = len(self.paned_window.panes())
            print(f"[DEBUG] 現在のパネル数: {len(self.panes)}, パネル数: {sash_count}")
            # 分割バーの数はパネル数-1
            if sash_count > 1:
                sash_pos = self.paned_window.sashpos(0)
                print(f"[DEBUG] 分割バー0の位置: {sash_pos}")
            else:
                print(f"[DEBUG] 分割バーなし (パネル数: {sash_count})")
        except Exception as e:
            print(f"[DEBUG] 分割バー状態確認エラー: {e}")

    def pack(self, **kwargs):
        """パネルウィンドウをパック"""
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        self.paned_window.pack(**kwargs)

    def grid(self, **kwargs):
        """パネルウィンドウをグリッド配置"""
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        self.paned_window.grid(**kwargs)

    def configure_pane(self, index: int, **kwargs):
        """
        パネル設定

        Args:
            index: パネルインデックス
            **kwargs: 設定オプション
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        if 0 <= index < len(self.panes):
            self.paned_window.pane(self.panes[index], **kwargs)

    def get_pane_info(self, index: int) -> dict:
        """
        パネル情報取得

        Args:
            index: パネルインデックス

        Returns:
            パネル情報辞書
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        if 0 <= index < len(self.panes):
            return self.paned_window.pane(self.panes[index])
        return {}

    def set_sash_position(self, index: int, position: int):
        """
        分割バー位置設定

        Args:
            index: 分割バーインデックス（0が最初の分割バー）
            position: 位置（ピクセル）
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        try:
            self.paned_window.sashpos(index, position)
        except tk.TclError:
            # 分割バーが存在しない場合は無視
            pass

    def get_sash_position(self, index: int) -> int:
        """
        分割バー位置取得

        Args:
            index: 分割バーインデックス

        Returns:
            位置（ピクセル）
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        try:
            return self.paned_window.sashpos(index)
        except tk.TclError:
            return 0

    def bind_sash_motion(self, callback: Callable[[int, int], None]):
        """
        分割バードラッグ時のコールバック設定

        Args:
            callback: コールバック関数 (sash_index, position)
        """
        if self.paned_window is None:
            raise RuntimeError("PanedWindow is not initialized")

        def on_sash_motion(event):
            # どの分割バーがドラッグされているかを判定
            sash_index = 0  # 最初の分割バーのみサポート
            position = event.x if self.orientation == 'vertical' else event.y
            print(f"[DEBUG] 分割バードラッグ検出: sash_index={sash_index}, position={position}")
            callback(sash_index, position)

        # 分割バーのドラッグイベントをバインド
        self.paned_window.bind('<B1-Motion>', on_sash_motion)
        print(f"[DEBUG] 分割バードラッグイベントバインド完了: <B1-Motion>")

        # 分割バーがクリックされた時のイベントも追加
        def on_sash_click(event):
            print(f"[DEBUG] 分割バークリック検出: x={event.x}, y={event.y}")

        self.paned_window.bind('<Button-1>', on_sash_click)
        print(f"[DEBUG] 分割バークリックイベントバインド完了: <Button-1>")

        # 分割バーがリリースされた時のイベントも追加
        def on_sash_release(event):
            print(f"[DEBUG] 分割バーリリース検出: x={event.x}, y={event.y}")

        self.paned_window.bind('<ButtonRelease-1>', on_sash_release)
        print(f"[DEBUG] 分割バーリリースイベントバインド完了: <ButtonRelease-1>")

    def set_initial_sash_position(self):
        """分割バーの初期位置を設定"""
        if self.paned_window is None:
            return

        try:
            # ウィンドウのサイズを取得（複数回試行）
            for attempt in range(5):
                self.paned_window.update_idletasks()
                width = self.paned_window.winfo_width()
                height = self.paned_window.winfo_height()

                print(f"[DEBUG] PanedWindowサイズ (試行{attempt+1}): {width}x{height}")

                if width > 10 and height > 10:
                    break

                # サイズが取得できない場合は少し待機
                self.paned_window.after(100)

            # 分割バーの数が1つ以上ある場合
            panes = self.paned_window.panes()
            if len(panes) >= 2:
                if self.orientation == 'vertical':
                    # 垂直分割の場合、幅の中央に配置（最小200ピクセル）
                    initial_pos = max(width // 2, 200) if width > 0 else 300
                else:
                    # 水平分割の場合、高さの中央に配置（最小200ピクセル）
                    initial_pos = max(height // 2, 200) if height > 0 else 300

                # 分割バーの位置を設定
                self.paned_window.sashpos(0, initial_pos)
                print(f"[DEBUG] 分割バー初期位置設定: {initial_pos}")

                # 設定後の位置を確認
                actual_pos = self.paned_window.sashpos(0)
                print(f"[DEBUG] 設定後の分割バー位置: {actual_pos}")

                # 分割バーが表示されることを確認
                if actual_pos > 0:
                    print("[DEBUG] 分割バーが正常に設定されました")
                else:
                    print("[DEBUG] 警告: 分割バー位置が0のままです")

            else:
                print(f"[DEBUG] 分割バーが存在しません (パネル数: {len(panes)})")

        except Exception as e:
            print(f"[DEBUG] 分割バー初期位置設定エラー: {e}")

    def debug_sash_info(self):
        """分割バーの詳細情報をデバッグ出力"""
        if self.paned_window is None:
            print("[DEBUG] PanedWindowが初期化されていません")
            return

        try:
            # パネル数と分割バー数の確認
            panes = self.paned_window.panes()
            pane_count = len(panes)
            sash_count = pane_count - 1 if pane_count > 1 else 0

            print(f"[DEBUG] === 分割バー詳細情報 ===")
            print(f"[DEBUG] パネル数: {pane_count}")
            print(f"[DEBUG] 分割バー数: {sash_count}")

            # 各分割バーの位置を確認
            for i in range(sash_count):
                try:
                    pos = self.paned_window.sashpos(i)
                    print(f"[DEBUG] 分割バー{i}の位置: {pos}")
                except Exception as e:
                    print(f"[DEBUG] 分割バー{i}の位置取得エラー: {e}")

            # PanedWindowの設定を確認
            config = self.paned_window.configure()
            print(f"[DEBUG] PanedWindow設定:")
            for key, value in config.items():
                print(f"[DEBUG]   {key}: {value}")

            # スタイル情報を確認
            style = ttk.Style()
            print(f"[DEBUG] 現在のスタイル: {style.theme_use()}")

            # 分割バーのスタイルを確認
            try:
                sash_style = style.lookup('TPanedwindow', 'sashwidth')
                print(f"[DEBUG] 分割バー幅: {sash_style}")
            except Exception as e:
                print(f"[DEBUG] 分割バー幅取得エラー: {e}")

        except Exception as e:
            print(f"[DEBUG] 分割バー詳細情報取得エラー: {e}")

    def destroy(self):
        """コンポーネント破棄"""
        if self.paned_window:
            self.paned_window.destroy()
            self.paned_window = None
        self.panes.clear()
        self.weights.clear()
        self.min_sizes.clear()
