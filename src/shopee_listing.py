"""Safe Shopee SG listing preflight and payload construction.

The module deliberately defaults new items to ``UNLIST``.  A row must contain
real supplier/category/logistics/image data before it can be sent to Shopee.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


BLOCKED_PRODUCT_WORDS = (
    "medicine", "drug", "supplement", "eye drops",
    "医薬品", "目薬", "サプリ", "サプリメント",
)
PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net", "example-drugstore.example.com")
PLACEHOLDER_BRANDS = ("suncare japan", "eyecare plus", "test", "sample")


@dataclass
class ListingPreflightResult:
    ready: bool
    blockers: list[str] = field(default_factory=list)
    payload: dict[str, Any] | None = None


def _text(row: dict[str, Any], key: str) -> str:
    value = row.get(key, "")
    return "" if value is None else str(value).strip()


def _positive_float(row: dict[str, Any], key: str) -> float | None:
    try:
        value = float(row.get(key, 0))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def build_sg_unlisted_payload(row: dict[str, Any]) -> ListingPreflightResult:
    """Validate one master row and build an UNLIST payload when safe.

    Required Shopee-specific columns are intentionally explicit:
    ``shopee_sg_category_id``, ``shopee_sg_logistic_id`` and
    ``shopee_image_id``.  The image ID must come from Shopee's upload API;
    a local path or third-party URL is never sent directly to add_item.
    """
    blockers: list[str] = []
    name = _text(row, "product_name_en")
    description = _text(row, "description_en")
    brand = _text(row, "brand")
    source_url = _text(row, "source_url")
    combined = " ".join((name, description, _text(row, "product_name_jp"))).lower()

    if _text(row, "listing_status") != "READY_TO_LIST":
        blockers.append("商品検査がREADY_TO_LISTではありません")
    if any(word in combined for word in BLOCKED_PRODUCT_WORDS):
        blockers.append("医薬品・サプリメント等の除外対象です")
    if brand.lower() in PLACEHOLDER_BRANDS:
        blockers.append("テスト用ブランド名です")
    parsed = urlparse(source_url)
    if not source_url or parsed.hostname in PLACEHOLDER_HOSTS or (parsed.hostname or "").endswith(".example.com"):
        blockers.append("実在する仕入先URLが確認できません")

    price = _positive_float(row, "sg_price")
    weight_g = _positive_float(row, "shipping_weight_g")
    stock = _positive_float(row, "stock")
    if not name or not description or price is None or weight_g is None or stock is None:
        blockers.append("商品名・説明・価格・重量・在庫の必須項目が不足しています")

    try:
        category_id = int(row.get("shopee_sg_category_id", 0))
    except (TypeError, ValueError):
        category_id = 0
    try:
        logistic_id = int(row.get("shopee_sg_logistic_id", 0))
    except (TypeError, ValueError):
        logistic_id = 0
    image_id = _text(row, "shopee_image_id")
    if category_id <= 0:
        blockers.append("Shopee SGカテゴリIDが未設定です")
    if logistic_id <= 0:
        blockers.append("Shopee SG物流チャンネルIDが未設定です")
    if not image_id:
        blockers.append("Shopeeへアップロード済みの画像IDが未設定です")

    dims = {}
    for source, target in (
        ("package_height_cm", "package_height"),
        ("package_length_cm", "package_length"),
        ("package_width_cm", "package_width"),
    ):
        value = _positive_float(row, source)
        if value is None:
            blockers.append("梱包サイズが未確認です")
            dims = {}
            break
        dims[target] = int(round(value))

    if blockers:
        return ListingPreflightResult(False, list(dict.fromkeys(blockers)))

    payload: dict[str, Any] = {
        "original_price": price,
        "description": description,
        "description_type": "normal",
        "weight": round(weight_g / 1000.0, 3),
        "item_name": name,
        "item_status": "UNLIST",
        "dimension": dims,
        "logistic_info": [{"logistic_id": logistic_id, "enabled": True}],
        "category_id": category_id,
        "image": {"image_id_list": [image_id]},
        "item_sku": _text(row, "sku_sg"),
        "condition": "NEW",
        "brand": {"brand_id": 0, "original_brand_name": brand or "No Brand"},
        "seller_stock": [{"stock": int(stock)}],
    }
    return ListingPreflightResult(True, payload=payload)
