# CCTranslation

CCTranslation は Windows 常駐型のクリップボード翻訳ユーティリティ
です。`Ctrl + C` を素早く 2 回押すだけでクリップボードのテキスト
を自動翻訳し、Tkinter 製のポップアップウィンドウで結果を表示し
ます。翻訳処理には Google 翻訳 (translate.googleapis.com) の Web
API を利用し、翻訳元言語の自動検出および翻訳先言語の切り替えを
サポートしています。

## 主な機能

- **ダブルコピー検出**: `Ctrl + C` が既定の 0.5 秒以内に 2 回押さ
  れた場合のみ翻訳を実行します。間隔はコマンドラインオプション
  で変更可能です。
- **Tkinter ポップアップ UI**: 原文と訳文を 2 分割で表示し、検出
  言語・翻訳先言語・言語トグルを備えたコントロールエリアを提供
  します。ウィンドウはポインタ付近に再配置され、常に手前に表示
  されます。
- **バックグラウンド翻訳**: 翻訳処理は別スレッドで行われ、UI ス
  レッドをブロックしません。翻訳結果はキューを介して UI に渡さ
  れます。
- **システムトレイ連携 (任意)**: `pystray` と `Pillow` が利用で
  きる場合、システムトレイアイコンからウィンドウの表示や終了を
  行えます。
- **CLI モード**: `--once` オプションで単発翻訳を実行し、標準出
  力へ結果を表示できます。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`pyWinhook` と `pythoncom` は Windows 専用のため、Windows 以外で
はキーボードフック機能が無効化されます。単発翻訳やユニットテス
トは他プラットフォームでも実行可能です。

## 使い方

### 常駐モード

```bash
python translator_app.py --dest ja --src auto
```

初回起動時は単一インスタンスガードにより 1 つのプロセスだけが
常駐します。キーボードフックが利用できない場合はエラーが表示さ
れます。

### 単発翻訳

```bash
python translator_app.py --once --dest en
```

クリップボードのテキストを翻訳し、標準出力に結果を表示します。

## テスト

```bash
pytest
```

## ライセンス

MIT License
