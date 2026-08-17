"""
title_generator.py
---------------------
V2仕様3の実装。

旧版の問題: 英語タイトルに日本語が混ざる
  例: "Curel キュレル 潤浸保湿フェイスクリーム 40g Japan" (不可)

このモジュールは英語タイトルを自動翻訳で「生成」しません。
確認できない英語商品名を勝手に作ることは仕様で禁止されているため、
商品マスターの product_name_en 列に入力された値を検証するだけに留めます。
- 日本語文字(ひらがな/カタカナ/漢字)が含まれていれば無効
- 空であれば DATA_INCOMPLETE
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_JAPANESE_CHAR_RE = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"  # ひらがな/カタカナ/漢字
)


@dataclass
class TitleCheckResult:
    is_valid: bool
    reason: str


def validate_english_title(product_name_en: str) -> TitleCheckResult:
    product_name_en = (product_name_en or "").strip()

    if not product_name_en:
        return TitleCheckResult(
            is_valid=False,
            reason="DATA_INCOMPLETE: product_name_enが未入力です(自動生成は行いません)",
        )

    if _JAPANESE_CHAR_RE.search(product_name_en):
        return TitleCheckResult(
            is_valid=False,
            reason=(
                "product_name_enに日本語文字が含まれています。"
                "英語のみの商品名をproduct_name_en列に入力してください。"
            ),
        )

    return TitleCheckResult(is_valid=True, reason="OK")
