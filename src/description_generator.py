"""
description_generator.py
---------------------------
V2仕様4・14の実装。

- Made in Japan固定表示を廃止。country_of_originが確認できた場合のみ表示。
  Unknownの場合は原産国を断定しない(表示自体を省略)。
- 商品マスターに存在する事実だけを使用する。
- 医療効果等を断定する語句(cures/heals/treats等)を含めない。
- 不明な項目(空欄)は省略する。
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import FORBIDDEN_CLAIM_KEYWORDS


@dataclass
class DescriptionResult:
    text: str
    warnings: list[str]


def generate_description(row: dict) -> DescriptionResult:
    lines = []
    warnings: list[str] = []

    brand = (row.get("brand", "") or "").strip()
    product_name_en = (row.get("product_name_en", "") or "").strip()
    volume = (row.get("volume", "") or "").strip()
    country_of_origin = (row.get("country_of_origin", "") or "").strip()

    if brand:
        lines.append(f"Brand: {brand}")
    if product_name_en:
        lines.append(f"Product: {product_name_en}")
    if volume:
        lines.append(f"Size: {volume}")

    # country_of_originがUnknown/空の場合は原産国を断定表示しない(Made in Japan固定の廃止)
    if country_of_origin and country_of_origin.lower() != "unknown":
        lines.append(f"Country of Origin: {country_of_origin}")

    key_features = (row.get("key_features", "") or "").strip()
    if key_features:
        lines.append(f"Key Features: {key_features}")

    how_to_use = (row.get("how_to_use", "") or "").strip()
    if how_to_use:
        lines.append(f"How to Use: {how_to_use}")

    package_contents = (row.get("package_contents", "") or "").strip()
    if package_contents:
        lines.append(f"Package Contents: {package_contents}")

    lines.append("Ships from Japan")

    text = "\n".join(lines)

    lowered = text.lower()
    for kw in FORBIDDEN_CLAIM_KEYWORDS:
        if kw in lowered:
            warnings.append(f"禁止表現「{kw}」が含まれています。説明文から削除してください。")

    return DescriptionResult(text=text, warnings=warnings)
