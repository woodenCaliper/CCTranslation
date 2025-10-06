"""
Double Copy Detector - ダブルコピー検出システム

Ctrl+C の連続押下を検出する
"""

import time
from typing import Optional, Callable


class DoubleCopyDetector:
    """ダブルコピー検出クラス"""

    def __init__(self, interval: float = 0.5):
        """
        ダブルコピー検出の初期化

        Args:
            interval: ダブルコピー検出間隔（秒）
        """
        self.interval = interval
        self.last_copy_time: Optional[float] = None
        self.callback: Optional[Callable] = None

    def set_callback(self, callback: Callable) -> None:
        """
        ダブルコピー検出時のコールバック関数を設定

        Args:
            callback: コールバック関数
        """
        self.callback = callback

    def detect_copy(self) -> bool:
        """
        コピー操作を検出

        Returns:
            ダブルコピーが検出された場合はTrue
        """
        current_time = time.time()

        if self.last_copy_time is not None:
            # 前回のコピーからの経過時間を計算
            elapsed_time = current_time - self.last_copy_time

            if elapsed_time <= self.interval:
                # ダブルコピー検出
                self.last_copy_time = None  # リセット
                if self.callback:
                    self.callback()
                return True

        # コピー時間を記録
        self.last_copy_time = current_time
        return False

    def reset(self) -> None:
        """検出状態をリセット"""
        self.last_copy_time = None

    def set_interval(self, interval: float) -> None:
        """
        検出間隔を設定

        Args:
            interval: 新しい検出間隔（秒）
        """
        self.interval = interval
