"""
Language Manager - 言語データ管理システム

言語データの読み込み、変換、管理を行う
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class LanguageManager:
    """言語データ管理クラス"""

    def __init__(self, languages_file: Optional[str] = None):
        """
        言語管理の初期化

        Args:
            languages_file: 言語データファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if languages_file is None:
            # プロジェクトルートのdata/languages.jsonを使用
            project_root = Path(__file__).parent.parent.parent
            languages_file = project_root / "data" / "languages.json"

        self.languages_file = Path(languages_file)
        self.languages_data = {}
        self.languages = {}
        self.language_groups = {}
        self.language_pairs = {}
        self._load_languages()

    def _load_languages(self) -> None:
        """言語データの読み込み"""
        try:
            if self.languages_file.exists():
                with open(self.languages_file, 'r', encoding='utf-8') as f:
                    self.languages_data = json.load(f)

                self.languages = self.languages_data.get('languages', {})
                self.language_groups = self.languages_data.get('language_groups', {})
                self.language_pairs = self.languages_data.get('language_pairs', {})

                print(f"言語データを読み込みました: {len(self.languages)}言語")
            else:
                print(f"言語データファイルが見つかりません: {self.languages_file}")
                self._create_default_languages()
        except Exception as e:
            print(f"言語データの読み込みに失敗しました: {e}")
            self._create_default_languages()

    def _create_default_languages(self) -> None:
        """デフォルト言語データの作成"""
        self.languages = {
            "auto": "自動検出",
            "ja": "日本語",
            "en": "英語",
            "zh": "中国語",
            "ko": "韓国語",
            "es": "スペイン語",
            "fr": "フランス語",
            "de": "ドイツ語"
        }

        self.language_groups = {
            "major_languages": ["ja", "en", "zh", "ko", "es", "fr", "de"]
        }

        self.language_pairs = {
            "common_pairs": [
                {"from": "auto", "to": "ja", "description": "任意言語 → 日本語"},
                {"from": "auto", "to": "en", "description": "任意言語 → 英語"},
                {"from": "ja", "to": "en", "description": "日本語 → 英語"},
                {"from": "en", "to": "ja", "description": "英語 → 日本語"}
            ]
        }

    def get_language_name(self, language_code: str) -> str:
        """
        言語コードから言語名を取得

        Args:
            language_code: 言語コード（例: 'ja', 'en'）

        Returns:
            言語名（見つからない場合は言語コードをそのまま返す）
        """
        return self.languages.get(language_code, language_code)

    def get_language_code(self, language_name: str) -> Optional[str]:
        """
        言語名から言語コードを取得

        Args:
            language_name: 言語名

        Returns:
            言語コード（見つからない場合はNone）
        """
        for code, name in self.languages.items():
            if name == language_name:
                return code
        return None

    def get_all_languages(self) -> Dict[str, str]:
        """全言語の辞書を取得"""
        return self.languages.copy()

    def get_language_list(self) -> List[Tuple[str, str]]:
        """言語のリストを取得（コード、名前のタプルのリスト）"""
        return [(code, name) for code, name in self.languages.items()]

    def get_major_languages(self) -> List[Tuple[str, str]]:
        """主要言語のリストを取得"""
        major_codes = self.language_groups.get('major_languages', ['ja', 'en', 'zh', 'ko', 'es', 'fr', 'de'])
        return [(code, self.get_language_name(code)) for code in major_codes if code in self.languages]

    def get_language_group(self, group_name: str) -> List[Tuple[str, str]]:
        """
        指定された言語グループのリストを取得

        Args:
            group_name: グループ名（'major_languages', 'european_languages'等）

        Returns:
            言語のリスト（コード、名前のタプルのリスト）
        """
        group_codes = self.language_groups.get(group_name, [])
        return [(code, self.get_language_name(code)) for code in group_codes if code in self.languages]

    def get_common_language_pairs(self) -> List[Dict[str, str]]:
        """一般的な言語ペアのリストを取得"""
        return self.language_pairs.get('common_pairs', [])

    def is_valid_language_code(self, language_code: str) -> bool:
        """言語コードが有効かチェック"""
        return language_code in self.languages

    def get_auto_detect_languages(self) -> List[Tuple[str, str]]:
        """自動検出可能な言語のリストを取得（auto以外）"""
        return [(code, name) for code, name in self.languages.items() if code != 'auto']

    def get_supported_languages_for_translation(self) -> List[Tuple[str, str]]:
        """翻訳でサポートされている言語のリストを取得"""
        # Google翻訳でサポートされている主要言語のみを返す
        supported_codes = [
            'auto', 'ja', 'en', 'zh', 'ko', 'es', 'fr', 'de', 'it', 'pt', 'ru',
            'ar', 'hi', 'th', 'vi', 'id', 'tr', 'pl', 'nl', 'sv', 'da', 'no',
            'fi', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl', 'et', 'lv', 'lt',
            'el', 'he', 'fa', 'ur', 'bn', 'ta', 'te', 'ml', 'kn', 'gu', 'pa',
            'or', 'as', 'ne', 'si', 'my', 'km', 'lo', 'ka', 'am', 'sw', 'zu',
            'af', 'sq', 'eu', 'be', 'bs', 'ca', 'cy', 'eo', 'ga', 'is', 'mk',
            'mt', 'uk', 'uz', 'az', 'kk', 'ky', 'mn', 'tg', 'tk', 'hy', 'yi'
        ]
        return [(code, self.get_language_name(code)) for code in supported_codes if code in self.languages]

    def get_language_family(self, language_code: str) -> Optional[str]:
        """
        言語の語族を取得

        Args:
            language_code: 言語コード

        Returns:
            語族名（見つからない場合はNone）
        """
        # 主要な語族の分類
        language_families = {
            # 日本語
            'ja': 'Japanese',
            # 中国語
            'zh': 'Sino-Tibetan',
            # 韓国語
            'ko': 'Koreanic',
            # インド・ヨーロッパ語族
            'en': 'Indo-European',
            'es': 'Indo-European',
            'fr': 'Indo-European',
            'de': 'Indo-European',
            'it': 'Indo-European',
            'pt': 'Indo-European',
            'ru': 'Indo-European',
            'hi': 'Indo-European',
            'ar': 'Afro-Asiatic',
            'he': 'Afro-Asiatic',
            'fa': 'Indo-European',
            'ur': 'Indo-European',
            'tr': 'Turkic',
            'ko': 'Koreanic',
            'th': 'Tai-Kadai',
            'vi': 'Austroasiatic',
            'id': 'Austronesian',
            'ms': 'Austronesian',
            'tl': 'Austronesian'
        }
        return language_families.get(language_code)

    def get_difficulty_level(self, language_code: str) -> Optional[str]:
        """
        日本語話者にとっての言語習得難易度を取得

        Args:
            language_code: 言語コード

        Returns:
            難易度レベル（'easy', 'medium', 'hard'）
        """
        # 日本語話者にとっての難易度分類
        difficulty_levels = {
            # 簡単（似ている言語）
            'ko': 'easy',  # 韓国語
            'zh': 'easy',  # 中国語（漢字共通）

            # 中程度
            'en': 'medium',  # 英語
            'es': 'medium',  # スペイン語
            'fr': 'medium',  # フランス語
            'de': 'medium',  # ドイツ語
            'it': 'medium',  # イタリア語
            'pt': 'medium',  # ポルトガル語
            'nl': 'medium',  # オランダ語
            'sv': 'medium',  # スウェーデン語
            'da': 'medium',  # デンマーク語
            'no': 'medium',  # ノルウェー語

            # 難しい（異なる語族）
            'ar': 'hard',  # アラビア語
            'he': 'hard',  # ヘブライ語
            'hi': 'hard',  # ヒンディー語
            'th': 'hard',  # タイ語
            'vi': 'hard',  # ベトナム語
            'ru': 'hard',  # ロシア語
            'tr': 'hard',  # トルコ語
            'fa': 'hard',  # ペルシャ語
            'ur': 'hard',  # ウルドゥー語
        }
        return difficulty_levels.get(language_code)

    def get_language_info(self, language_code: str) -> Dict[str, str]:
        """
        言語の詳細情報を取得

        Args:
            language_code: 言語コード

        Returns:
            言語情報の辞書
        """
        info = {
            'code': language_code,
            'name': self.get_language_name(language_code),
            'family': self.get_language_family(language_code),
            'difficulty': self.get_difficulty_level(language_code)
        }
        return info

    def save_languages(self) -> None:
        """言語データをファイルに保存"""
        try:
            data = {
                'languages': self.languages,
                'language_groups': self.language_groups,
                'language_pairs': self.language_pairs
            }

            # ディレクトリが存在しない場合は作成
            self.languages_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.languages_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"言語データを保存しました: {self.languages_file}")
        except Exception as e:
            print(f"言語データの保存に失敗しました: {e}")


# テスト用
if __name__ == "__main__":
    lang_manager = LanguageManager()

    print("=== 言語データ管理テスト ===")
    print(f"総言語数: {len(lang_manager.get_all_languages())}")

    print("\n--- 主要言語 ---")
    major_langs = lang_manager.get_major_languages()
    for code, name in major_langs:
        print(f"{code}: {name}")

    print("\n--- 言語情報 ---")
    test_codes = ['ja', 'en', 'zh', 'ko', 'ar', 'hi']
    for code in test_codes:
        info = lang_manager.get_language_info(code)
        print(f"{code}: {info}")

    print("\n--- 一般的な言語ペア ---")
    pairs = lang_manager.get_common_language_pairs()
    for pair in pairs:
        print(f"{pair['from']} → {pair['to']}: {pair['description']}")

    print("\n--- 語族情報 ---")
    for code in ['ja', 'en', 'zh', 'ko', 'ar', 'hi']:
        family = lang_manager.get_language_family(code)
        difficulty = lang_manager.get_difficulty_level(code)
        print(f"{code}: {family} ({difficulty})")
