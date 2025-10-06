"""
Single Instance Manager - 多重起動防止システム

アプリケーションの単一インスタンス動作を保証するためのユーティリティ
"""

import os
import sys
import tempfile
import atexit
import psutil
import time
from typing import Optional
import logging


class SingleInstanceManager:
    """アプリケーションの単一インスタンス管理クラス"""

    def __init__(self, app_name: str = "CCTranslation"):
        """
        初期化

        Args:
            app_name: アプリケーション名（ロックファイル名に使用）
        """
        self.app_name = app_name
        self.lock_file_path = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.lock_file: Optional[object] = None
        self.logger = logging.getLogger(__name__)
        self.timeout_seconds = 10  # ロックファイルのタイムアウト時間（秒）

    def is_already_running(self) -> bool:
        """
        既にアプリケーションが実行中かどうかをチェック

        Returns:
            bool: 既に実行中の場合True
        """
        try:
            # ロックファイルの存在チェック
            if os.path.exists(self.lock_file_path):
                try:
                    # ロックファイルの作成時間をチェック
                    lock_file_age = time.time() - os.path.getctime(self.lock_file_path)
                    if lock_file_age > self.timeout_seconds:
                        # タイムアウト時間を過ぎている場合は古いロックファイルとみなす
                        self.logger.info(f"古いロックファイルを検出（{lock_file_age:.1f}秒経過）。削除します。")
                        self._cleanup_old_lock_file()
                        return False

                    # プロセスIDを読み取り
                    with open(self.lock_file_path, 'r') as f:
                        pid_str = f.read().strip()

                    try:
                        pid = int(pid_str)
                        # プロセスが実際に存在するかチェック
                        if psutil.pid_exists(pid):
                            try:
                                process = psutil.Process(pid)
                                # Pythonプロセスで、かつコマンドラインにアプリ名が含まれているかチェック
                                if process.name().lower() == 'python.exe':
                                    cmdline = ' '.join(process.cmdline())
                                    if self.app_name.lower() in cmdline.lower():
                                        self.logger.warning(f"アプリケーションは既に実行中です (PID: {pid})")
                                        return True

                                # プロセス名が一致しない場合は古いロックファイルとみなす
                                self.logger.info(f"PID {pid}のプロセス名が一致しません（{process.name()}）。古いロックファイルを削除します。")
                                self._cleanup_old_lock_file()
                                return False

                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # プロセスが存在しないかアクセスできない場合は古いロックファイル
                                self.logger.info(f"PID {pid}のプロセスにアクセスできません。古いロックファイルを削除します。")
                                self._cleanup_old_lock_file()
                                return False
                        else:
                            # プロセスが存在しない場合は古いロックファイル
                            self.logger.info(f"PID {pid}のプロセスが存在しません。古いロックファイルを削除します。")
                            self._cleanup_old_lock_file()
                            return False

                    except ValueError:
                        # PIDが無効な場合は古いロックファイル
                        self.logger.info("無効なロックファイルを削除しました")
                        self._cleanup_old_lock_file()
                        return False

                except PermissionError:
                    # ロックファイルが他のプロセスによって使用されている場合
                    # これは既存のインスタンスが実行中であることを示す
                    self.logger.warning(f"ロックファイルが他のプロセスによって使用されています: {self.lock_file_path}")

                    # ロックファイルの内容を確認してみる
                    try:
                        with open(self.lock_file_path, 'r') as f:
                            pid_str = f.read().strip()
                        try:
                            pid = int(pid_str)
                            if psutil.pid_exists(pid):
                                # プロセスが存在する場合は実行中とみなす
                                try:
                                    process = psutil.Process(pid)
                                    if process.name().lower() == 'python.exe':
                                        cmdline = ' '.join(process.cmdline())
                                        if self.app_name.lower() in cmdline.lower():
                                            return True
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                        except ValueError:
                            pass
                    except Exception:
                        pass

                    return True
                except Exception as e:
                    self.logger.error(f"ロックファイル読み取りエラー: {e}")
                    return False

            return False

        except Exception as e:
            self.logger.error(f"既存インスタンスチェックエラー: {e}")
            return False

    def _cleanup_old_lock_file(self):
        """古いロックファイルを削除"""
        try:
            if os.path.exists(self.lock_file_path):
                # ファイルが使用中でないかチェック
                try:
                    with open(self.lock_file_path, 'r') as f:
                        f.read()
                    # ファイルが読み取れる場合は削除
                    os.remove(self.lock_file_path)
                    self.logger.info(f"古いロックファイルを削除: {self.lock_file_path}")
                except PermissionError:
                    # ファイルが使用中の場合は無視（別のプロセスが使用中）
                    self.logger.warning(f"ロックファイルが使用中のため削除をスキップ: {self.lock_file_path}")
                    return False
        except Exception as e:
            self.logger.error(f"古いロックファイル削除エラー: {e}")
            return False
        return True

    def acquire_lock(self) -> bool:
        """
        ロックを取得して単一インスタンスを保証

        Returns:
            bool: ロック取得成功の場合True、既に実行中の場合はFalse
        """
        try:
            # 既存インスタンスチェック
            if self.is_already_running():
                return False

            # 古いロックファイルをクリーンアップ
            if not self._cleanup_old_lock_file():
                # クリーンアップに失敗した場合は既存インスタンスが実行中とみなす
                return False

            # ロックファイルを作成
            try:
                self.lock_file = open(self.lock_file_path, 'w')
                self.lock_file.write(str(os.getpid()))
                self.lock_file.flush()

                # 終了時のクリーンアップを登録
                atexit.register(self.release_lock)

                self.logger.info(f"単一インスタンスロックを取得しました (PID: {os.getpid()})")
                return True
            except PermissionError:
                # ロックファイルの作成に失敗した場合は既存インスタンスが実行中とみなす
                self.logger.warning(f"ロックファイルの作成に失敗しました: {self.lock_file_path}")
                return False

        except Exception as e:
            self.logger.error(f"ロック取得エラー: {e}")
            return False

    def release_lock(self):
        """ロックを解放"""
        try:
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None

            if os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
                self.logger.info("単一インスタンスロックを解放しました")

        except Exception as e:
            self.logger.error(f"ロック解放エラー: {e}")

    def show_already_running_message(self):
        """既に実行中であることをユーザーに通知"""
        try:
            import tkinter as tk
            from tkinter import messagebox

            # ルートウィンドウを作成（非表示）
            root = tk.Tk()
            root.withdraw()

            # メッセージボックスを表示
            messagebox.showwarning(
                "CCTranslation",
                "CCTranslationは既に実行中です。\n\n"
                "システムトレイを確認してください。\n"
                "または、タスクマネージャーから既存のプロセスを終了してから再起動してください。"
            )

            root.destroy()

        except Exception as e:
            self.logger.error(f"通知メッセージ表示エラー: {e}")
            # フォールバック：コンソールメッセージ
            print(f"\n{'='*60}")
            print(f"CCTranslation は既に実行中です")
            print(f"{'='*60}")
            print(f"システムトレイを確認してください。")
            print(f"または、タスクマネージャーから既存のプロセスを終了してから再起動してください。")
            print(f"{'='*60}\n")

    def check_and_exit_if_running(self) -> bool:
        """
        既存インスタンスをチェックし、実行中の場合は終了

        Returns:
            bool: 既存インスタンスが存在する場合True（終了する）
        """
        if self.is_already_running():
            self.show_already_running_message()
            return True
        return False


def check_single_instance(app_name: str = "CCTranslation") -> bool:
    """
    単一インスタンスチェックの簡易関数

    Args:
        app_name: アプリケーション名

    Returns:
        bool: 既存インスタンスが存在する場合True（終了すべき）
    """
    manager = SingleInstanceManager(app_name)
    return manager.check_and_exit_if_running()


if __name__ == "__main__":
    # テストコード
    print("=== Single Instance Manager テスト ===")

    # ログ設定
    logging.basicConfig(level=logging.INFO)

    manager = SingleInstanceManager("CCTranslation_Test")

    print("既存インスタンスチェック...")
    if manager.is_already_running():
        print("既存インスタンスが見つかりました")
        manager.show_already_running_message()
    else:
        print("既存インスタンスは見つかりませんでした")

        print("ロック取得...")
        if manager.acquire_lock():
            print("ロック取得成功")
            input("Enterキーを押すとロックを解放します...")
            manager.release_lock()
            print("ロック解放完了")
        else:
            print("ロック取得失敗")
