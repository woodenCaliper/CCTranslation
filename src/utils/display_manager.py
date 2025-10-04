"""
Display Manager - ディスプレイ管理システム

複数ディスプレイ環境でのマウス位置取得とウィンドウ配置を管理
"""

import tkinter as tk
from typing import Tuple, List, Optional
import logging


class DisplayManager:
    """ディスプレイ管理クラス"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._display_info = None
        self._displays = []  # 初期化を追加
        self._update_display_info()

    def _update_display_info(self):
        """ディスプレイ情報を更新"""
        try:
            # Windows APIを使用してディスプレイ情報を取得
            import win32api
            import win32con

            # モニター情報を取得
            monitors = win32api.EnumDisplayMonitors()
            self.logger.debug(f"検出されたモニター数: {len(monitors)}")

            self._displays = []
            for i, monitor in enumerate(monitors):
                try:
                    # モニターの矩形情報を取得
                    # monitor[0] = PyHANDLE, monitor[1] = PyHANDLE, monitor[2] = (left, top, right, bottom)
                    monitor_rect = monitor[2]  # 実際の矩形情報は3番目の要素
                    device_name = monitor[1]   # デバイス名は2番目の要素

                    # 矩形情報からサイズを取得
                    # monitor_rectは(left, top, right, bottom)の形式のタプル
                    left, top, right, bottom = monitor_rect

                    width = right - left
                    height = bottom - top

                    display_info = {
                        'id': i,
                        'width': width,
                        'height': height,
                        'x': left,
                        'y': top,
                        'device_name': str(device_name)
                    }

                    self._displays.append(display_info)
                    self.logger.debug(f"ディスプレイ{i}: {width}x{height} at ({left}, {top})")

                except Exception as e:
                    self.logger.warning(f"ディスプレイ{i}の詳細情報取得エラー: {e}")
                    # フォールバック: デフォルト値を使用
                    display_info = {
                        'id': i,
                        'width': 1920,
                        'height': 1080,
                        'x': i * 1920,  # 横に並べる想定
                        'y': 0,
                        'device_name': f"Display_{i}"
                    }
                    self._displays.append(display_info)

            # メイン情報を設定
            if self._displays:
                # プライマリディスプレイ（通常は(0,0)にある）を特定
                primary_display = None
                for display in self._displays:
                    if display['x'] == 0 and display['y'] == 0:
                        primary_display = display
                        break

                if primary_display:
                    self._display_info = {
                        'screen_width': primary_display['width'],
                        'screen_height': primary_display['height'],
                        'screen_count': len(self._displays)
                    }
                else:
                    # プライマリディスプレイが見つからない場合は最初のディスプレイを使用
                    self._display_info = {
                        'screen_width': self._displays[0]['width'],
                        'screen_height': self._displays[0]['height'],
                        'screen_count': len(self._displays)
                    }
            else:
                # フォールバック
                self._display_info = {
                    'screen_width': 1920,
                    'screen_height': 1080,
                    'screen_count': 1
                }
                self._displays = [{
                    'id': 0,
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0
                }]

            self.logger.info(f"ディスプレイ情報更新完了: {len(self._displays)}台")
            for display in self._displays:
                self.logger.info(f"  ディスプレイ{display['id']}: {display['width']}x{display['height']} at ({display['x']}, {display['y']})")

        except Exception as e:
            self.logger.error(f"ディスプレイ情報取得エラー: {e}")
            # フォールバック: デフォルトの単一ディスプレイ情報
            self._display_info = {
                'screen_width': 1920,
                'screen_height': 1080,
                'screen_count': 1
            }
            self._displays = [{
                'id': 0,
                'width': 1920,
                'height': 1080,
                'x': 0,
                'y': 0
            }]

    def get_mouse_position(self) -> Tuple[int, int]:
        """
        現在のマウス位置を取得

        Returns:
            Tuple[int, int]: (x, y) 座標
        """
        try:
            # Windows APIを使用してマウス位置を取得
            import win32api
            cursor_pos = win32api.GetCursorPos()
            self.logger.debug(f"マウス位置: ({cursor_pos[0]}, {cursor_pos[1]})")
            return cursor_pos
        except Exception as e:
            self.logger.error(f"マウス位置取得エラー: {e}")
            # フォールバック: 画面中央
            return (self._display_info['screen_width'] // 2, self._display_info['screen_height'] // 2)

    def get_display_for_position(self, x: int, y: int) -> Optional[dict]:
        """
        指定された座標が属するディスプレイを取得

        Args:
            x: X座標
            y: Y座標

        Returns:
            dict: ディスプレイ情報、見つからない場合はNone
        """
        try:
            self.logger.debug(f"座標({x}, {y})のディスプレイ判定開始")

            for display in self._displays:
                display_left = display['x']
                display_top = display['y']
                display_right = display['x'] + display['width']
                display_bottom = display['y'] + display['height']

                self.logger.debug(f"  ディスプレイ{display['id']}: ({display_left}, {display_top}) - ({display_right}, {display_bottom})")

                if (display_left <= x < display_right and
                    display_top <= y < display_bottom):
                    self.logger.debug(f"座標({x}, {y})はディスプレイ{display['id']}に属します")
                    return display

            # 見つからない場合は、最も近いディスプレイを返す
            self.logger.warning(f"座標({x}, {y})に対応するディスプレイが見つかりません。最も近いディスプレイを選択します。")

            if not self._displays:
                return None

            # 各ディスプレイの中心点との距離を計算
            closest_display = None
            min_distance = float('inf')

            for display in self._displays:
                center_x = display['x'] + display['width'] // 2
                center_y = display['y'] + display['height'] // 2
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_display = display

            self.logger.debug(f"最も近いディスプレイ: {closest_display['id']} (距離: {min_distance:.1f})")
            return closest_display

        except Exception as e:
            self.logger.error(f"ディスプレイ判定エラー: {e}")
            return self._displays[0] if self._displays else None

    def calculate_popup_position(self, popup_width: int, popup_height: int,
                               mouse_x: int, mouse_y: int) -> Tuple[int, int]:
        """
        ポップアップウィンドウの最適な位置を計算

        Args:
            popup_width: ポップアップの幅
            popup_height: ポップアップの高さ
            mouse_x: マウスのX座標
            mouse_y: マウスのY座標

        Returns:
            Tuple[int, int]: (x, y) 座標
        """
        try:
            # マウス位置が属するディスプレイを取得
            display = self.get_display_for_position(mouse_x, mouse_y)
            if not display:
                # フォールバック: マウス位置をそのまま使用
                return (mouse_x, mouse_y)

            # ディスプレイの境界内に収まるように調整
            display_left = display['x']
            display_top = display['y']
            display_right = display['x'] + display['width']
            display_bottom = display['y'] + display['height']

            # 初期位置はマウス位置
            popup_x = mouse_x
            popup_y = mouse_y

            # 右端からはみ出る場合、左に移動
            if popup_x + popup_width > display_right:
                popup_x = display_right - popup_width - 10

            # 下端からはみ出る場合、上に移動
            if popup_y + popup_height > display_bottom:
                popup_y = display_bottom - popup_height - 10

            # 左端からはみ出る場合、右に移動
            if popup_x < display_left:
                popup_x = display_left + 10

            # 上端からはみ出る場合、下に移動
            if popup_y < display_top:
                popup_y = display_top + 10

            # 最小値を確保
            popup_x = max(display_left + 10, popup_x)
            popup_y = max(display_top + 10, popup_y)

            self.logger.debug(f"ポップアップ位置計算: マウス({mouse_x}, {mouse_y}) -> ポップアップ({popup_x}, {popup_y})")
            return (popup_x, popup_y)

        except Exception as e:
            self.logger.error(f"ポップアップ位置計算エラー: {e}")
            # フォールバック: マウス位置をそのまま使用
            return (mouse_x, mouse_y)

    def get_display_info(self) -> dict:
        """
        ディスプレイ情報を取得

        Returns:
            dict: ディスプレイ情報
        """
        return self._display_info

    def get_displays(self) -> List[dict]:
        """
        全ディスプレイの情報を取得

        Returns:
            List[dict]: ディスプレイ情報のリスト
        """
        return self._displays

    def refresh_display_info(self):
        """ディスプレイ情報を再取得"""
        self._update_display_info()


if __name__ == "__main__":
    # テストコード
    import logging
    logging.basicConfig(level=logging.DEBUG)

    dm = DisplayManager()

    print("=== Display Manager テスト ===")
    print(f"ディスプレイ情報: {dm.get_display_info()}")
    print(f"ディスプレイ一覧: {dm.get_displays()}")

    mouse_pos = dm.get_mouse_position()
    print(f"マウス位置: {mouse_pos}")

    popup_pos = dm.calculate_popup_position(400, 300, mouse_pos[0], mouse_pos[1])
    print(f"ポップアップ位置: {popup_pos}")
