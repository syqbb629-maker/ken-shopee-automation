"""
product_validator.py
-----------------------
V2仕様15・16・17・18の実装。

商品マスター1行を受け取り、以下の順で判定して listing_status を決定する。
1. 医薬品・サプリ等の検出 -> REGULATION_REVIEW_REQUIRED
2. エアゾール・危険物の検出 -> SHIPPING_REVIEW_REQUIRED
3. 在庫状態(UNKNOWN/OUT_OF_STOCK) -> OUT_OF_STOCK扱い
4. 英語タイトル検証(title_generator) -> 不備ならDATA_INCOMPLETE
5. 重量情報(weight_source=estimated) -> WEIGHT_REVIEW_REQUIRED
6. 画像(image_checker) -> IMAGE_REVIEW_REQUIRED
7. 送料・利益(profit_calculator) -> SHIPPING_RATE_MISSING / LOW_PROFIT / DATA_INCOMPLETE
8. 上記すべてクリアし、必須項目が揃っていれば READY_TO_LIST

1つでも不足したらREADYにしない(仕様17)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config import ListingStatus, StockStatus, WeightSource, Settings
from .schema import REGULATED_KEYWORDS_EN, REGULATED_KEYWORDS_JP, HAZARDOUS_KEYWORDS_EN
from .title_generator import validate_english_title
from .image_checker import evaluate_image
from .profit_calculator import ProfitResult, calculate_profit, ShippingRate


def _text_for_scan(row: dict) -> str:
    fields = [
        "product_name_jp", "product_name_en", "category",
        "key_features", "how_to_use", "description_en",
    ]
    return " ".join((row.get(f, "") or "") for f in fields).lower()


def detect_regulated(row: dict) -> bool:
    text = _text_for_scan(row)
    for kw in REGULATED_KEYWORDS_EN:
        if kw in text:
            return True
    for kw in REGULATED_KEYWORDS_JP:
        if kw in text:
            return True
    return False


def detect_hazardous(row: dict) -> bool:
    text = _text_for_scan(row)
    for kw in HAZARDOUS_KEYWORDS_EN:
        if kw in text:
            return True
    return False


@dataclass
class ValidationResult:
    listing_status: str
    reasons: list[str] = field(default_factory=list)
    profit_sg: ProfitResult | None = None
    profit_my: ProfitResult | None = None

    def add(self, reason: str) -> None:
        self.reasons.append(reason)


def _to_float(val) -> float | None:
    try:
        if val is None or str(val).strip() == "":
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


REQUIRED_TEXT_FIELDS = [
    "product_name_jp", "brand", "category", "description_en",
    "source_store", "source_url", "sku_sg", "sku_my",
]


def validate_product(
    row: dict,
    *,
    shipping_rates: list[ShippingRate],
    settings: Settings,
) -> ValidationResult:
    result = ValidationResult(listing_status=ListingStatus.READY_TO_LIST)

    # 1. 規制商品チェック(最優先・仕様15)
    if detect_regulated(row):
        result.listing_status = ListingStatus.REGULATION_REVIEW_REQUIRED
        result.add("医薬品/サプリ等に該当するキーワードを検出しました")
        return result

    # 2. 危険物・エアゾールチェック(仕様16)
    if detect_hazardous(row):
        result.listing_status = ListingStatus.SHIPPING_REVIEW_REQUIRED
        result.add("エアゾール/危険物に該当するキーワードを検出しました")
        return result

    # 3. 停止候補は最優先で維持
    if (row.get("listing_status", "") or "").strip() == ListingStatus.STOP_CANDIDATE:
        result.listing_status = ListingStatus.STOP_CANDIDATE
        result.add("停止候補として維持されています")
        return result

    # 4. 在庫状態
    stock_status = (row.get("source_stock_status", "") or "").strip().upper()
    if stock_status in (StockStatus.UNKNOWN, "", StockStatus.OUT_OF_STOCK):
        result.listing_status = ListingStatus.OUT_OF_STOCK
        result.add(f"在庫状態が不可({stock_status or '未設定'})です")
        return result

    # 5. 必須テキスト項目
    missing_text = [f for f in REQUIRED_TEXT_FIELDS if not (row.get(f, "") or "").strip()]
    purchase_price = _to_float(row.get("purchase_price_jpy"))
    if missing_text or purchase_price is None:
        result.listing_status = ListingStatus.DATA_INCOMPLETE
        if missing_text:
            result.add(f"必須項目が未入力です: {', '.join(missing_text)}")
        if purchase_price is None:
            result.add("purchase_price_jpyが未入力です")
        return result

    # 6. 英語タイトル検証
    title_check = validate_english_title(row.get("product_name_en", ""))
    if not title_check.is_valid:
        result.listing_status = ListingStatus.DATA_INCOMPLETE
        result.add(title_check.reason)
        return result

    # 7. 重量・梱包サイズ
    net_weight = _to_float(row.get("net_weight_g"))
    shipping_weight = _to_float(row.get("shipping_weight_g"))
    dims = [
        _to_float(row.get("package_length_cm")),
        _to_float(row.get("package_width_cm")),
        _to_float(row.get("package_height_cm")),
    ]
    weight_source = (row.get("weight_source", "") or "").strip().lower()

    if shipping_weight is None or net_weight is None or any(d is None for d in dims):
        result.listing_status = ListingStatus.WEIGHT_REVIEW_REQUIRED
        result.add("重量または梱包サイズが未入力です")
        return result

    if weight_source == WeightSource.ESTIMATED or weight_source not in (
        WeightSource.MANUFACTURER, WeightSource.SUPPLIER, WeightSource.MANUAL,
    ):
        result.listing_status = ListingStatus.WEIGHT_REVIEW_REQUIRED
        result.add(f"weight_sourceが未確認です(現在値: {weight_source or '未設定'})")
        return result

    # 8. 画像チェック
    image_result = evaluate_image(row)
    if not image_result.passes:
        result.listing_status = ListingStatus.IMAGE_REVIEW_REQUIRED
        result.add(f"画像条件を満たしていません: {image_result.reason}")
        return result

    # 9. 利益計算(SG/MY双方)
    sg_price = _to_float(row.get("sg_price"))
    my_price = _to_float(row.get("my_price"))

    profit_sg = calculate_profit(
        market="SG",
        sell_price_local=sg_price,
        purchase_price_jpy=purchase_price,
        shipping_weight_g=shipping_weight,
        rates=shipping_rates,
        settings=settings,
    )
    profit_my = calculate_profit(
        market="MY",
        sell_price_local=my_price,
        purchase_price_jpy=purchase_price,
        shipping_weight_g=shipping_weight,
        rates=shipping_rates,
        settings=settings,
    )
    result.profit_sg = profit_sg
    result.profit_my = profit_my

    for market_name, pr in (("SG", profit_sg), ("MY", profit_my)):
        if pr.status == "CONFIG_MISSING":
            result.listing_status = ListingStatus.CONFIG_MISSING
            result.add(f"{market_name}: {pr.detail}")
            return result
        if pr.status == "SHIPPING_RATE_MISSING":
            result.listing_status = ListingStatus.SHIPPING_RATE_MISSING
            result.add(f"{market_name}: {pr.detail}")
            return result
        if pr.status == "DATA_INCOMPLETE":
            result.listing_status = ListingStatus.DATA_INCOMPLETE
            result.add(f"{market_name}: {pr.detail}")
            return result

    if profit_sg.profit_jpy is not None and profit_sg.profit_jpy <= 0:
        result.listing_status = ListingStatus.LOW_PROFIT
        result.add(f"SG利益が0以下です({profit_sg.profit_jpy}円)")
        return result
    if profit_my.profit_jpy is not None and profit_my.profit_jpy <= 0:
        result.listing_status = ListingStatus.LOW_PROFIT
        result.add(f"MY利益が0以下です({profit_my.profit_jpy}円)")
        return result

    # すべての条件を満たした
    result.listing_status = ListingStatus.READY_TO_LIST
    result.add("全条件を満たしました")
    return result
