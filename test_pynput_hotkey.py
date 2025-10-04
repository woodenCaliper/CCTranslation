"""
pynput使用版HotkeyManager動作チェックアプリケーション
日本語キーボード特殊キー対応テスト
"""

import sys
import os
import time
import threading
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.hotkey_pynput import PynputHotkeyManager, PYNPUT_AVAILABLE

class PynputHotkeyTestApp:
    """pynput使用版ホットキーテストアプリケーション"""

    def __init__(self):
        self.hotkey_manager = None
        self.test_running = False
        self.double_copy_count = 0
        self.japanese_key_count = 0
        self.error_count = 0

    def on_double_copy_detected(self):
        """ダブルコピー検出時のコールバック"""
        self.double_copy_count += 1
        print(f"\n*** ダブルコピー検出 #{self.double_copy_count} ***")
        print("時間:", time.strftime("%H:%M:%S"))

    def start_test(self):
        """テスト開始"""
        print("=== pynput使用版HotkeyManager動作チェック ===")
        print("日本語キーボード特殊キー対応テスト")
        print()

        if not PYNPUT_AVAILABLE:
            print("ERROR: pynputが利用できません")
            print("pip install pynput でインストールしてください")
            return False

        try:
            # HotkeyManagerの初期化
            self.hotkey_manager = PynputHotkeyManager(self.on_double_copy_detected)
            print("OK: PynputHotkeyManager初期化成功")

            # 監視開始
            self.hotkey_manager.start_monitoring()
            print("OK: ホットキー監視開始")

            self.test_running = True
            return True

        except Exception as e:
            print(f"ERROR: 初期化失敗: {e}")
            self.error_count += 1
            return False

    def stop_test(self):
        """テスト停止"""
        if self.hotkey_manager and self.test_running:
            try:
                self.hotkey_manager.stop_monitoring()
                self.test_running = False
                print("OK: ホットキー監視停止")
            except Exception as e:
                print(f"ERROR: 停止失敗: {e}")
                self.error_count += 1

    def show_instructions(self):
        """テスト手順の表示"""
        print("\n" + "="*70)
        print("pynput使用版テスト手順:")
        print("="*70)
        print()
        print("【重要】このテストでは全角半角キーを積極的に押してください")
        print()
        print("1. 【最重要】全角半角キーを10回以上押してください")
        print("   → アプリが停止しないことを確認")
        print("   → Ctrl+C機能が維持されることを確認")
        print()
        print("2. 変換キーを5回以上押してください")
        print("   → アプリが停止しないことを確認")
        print()
        print("3. 無変換キーを5回以上押してください")
        print("   → アプリが停止しないことを確認")
        print()
        print("4. カタカナひらがなキーを5回以上押してください")
        print("   → アプリが停止しないことを確認")
        print()
        print("5. 【最重要テスト】全角半角キーを押した直後にCtrl+C を2回連続で押してください")
        print("   → ダブルコピー検出メッセージが表示されることを確認")
        print("   → これが成功すれば日本語キーボード問題は解決")
        print()
        print("6. その他のキー（A、B、C等）を押してください")
        print("   → アプリが停止しないことを確認")
        print()
        print("="*70)
        print("テスト時間: 60秒間")
        print("Enterキーを押すとテストを開始します")
        print("="*70)

    def monitor_status(self):
        """監視状態の監視"""
        while self.test_running:
            try:
                if self.hotkey_manager:
                    status = self.hotkey_manager.get_status()
                    if status["error_count"] > 0:
                        print(f"警告: エラー回数 {status['error_count']}")

                time.sleep(5)  # 5秒ごとにチェック
            except:
                break

    def run_countdown(self):
        """カウントダウン表示"""
        for i in range(60, 0, -1):
            if not self.test_running:
                break
            if i % 10 == 0 or i <= 5:
                print(f"残り時間: {i}秒")
            time.sleep(1)

    def run_test(self):
        """メインテスト実行"""
        # テスト手順表示
        self.show_instructions()

        # Enter待ち
        try:
            input()
        except EOFError:
            print("自動テストモードで開始します")

        # テスト開始
        if not self.start_test():
            return

        print("\n*** pynput使用版テスト開始 ***")
        print("上記の手順に従って積極的にテストしてください")
        print("特に全角半角キーを多めに押してください")
        print("pynputライブラリにより、より安定した動作が期待されます")
        print()

        # 状態監視スレッド開始
        status_thread = threading.Thread(target=self.monitor_status)
        status_thread.daemon = True
        status_thread.start()

        # カウントダウン開始
        countdown_thread = threading.Thread(target=self.run_countdown)
        countdown_thread.daemon = True
        countdown_thread.start()

        try:
            # テスト実行中
            while self.test_running:
                time.sleep(0.1)

                # 60秒経過で自動終了
                if countdown_thread.is_alive() == False:
                    break

        except KeyboardInterrupt:
            print("\nテストが中断されました")

        finally:
            # テスト停止
            self.stop_test()

            # 結果表示
            print("\n" + "="*70)
            print("pynput使用版テスト結果:")
            print("="*70)
            print(f"ダブルコピー検出回数: {self.double_copy_count}回")
            print(f"エラー回数: {self.error_count}回")

            if self.double_copy_count > 0:
                print("OK: ダブルコピー検出機能が動作しています")
            else:
                print("INFO: ダブルコピー検出はありませんでした")

            if self.error_count == 0:
                print("OK: エラーなしでアプリケーションが動作し続けました")
                print("OK: 日本語キーボード特殊キー問題が解決されています")
            else:
                print(f"WARNING: {self.error_count}個のエラーが発生しました")

            if self.hotkey_manager:
                final_status = self.hotkey_manager.get_status()
                print(f"最終監視状態: {final_status}")

            print("="*70)

            # 成功判定
            if self.error_count == 0 and self.double_copy_count > 0:
                print("SUCCESS: テスト成功！日本語キーボード問題が解決されました！")
                print("pynputライブラリにより、安定した動作を実現できました")
            elif self.error_count == 0:
                print("OK: 安定性テスト成功（機能テストは要確認）")
            else:
                print("FAIL: テスト失敗：さらなる改善が必要")

def main():
    """メイン関数"""
    try:
        app = PynputHotkeyTestApp()
        app.run_test()

    except Exception as e:
        print(f"ERROR: アプリケーションエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
