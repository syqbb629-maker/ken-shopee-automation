"""
profit_calculator.py
-----------------------
V2仕様6・7・13の実装。

- 固定送料(500円/600円)を廃止し、data/shipping_rates.csv から
  市場×重量帯で送料を検索する。
- 為替・Shopee手数料等はconfig.Settings(.env由来)から取得し、
  コードにハードコードしない。
- 利益 = 販売価格(JPY換算) - 仕入価格 - 国際送料 - Shopee手数料
          - 決済手数料 - その他経費
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Settings


@dataclass
class ShippingRate:
    market: str
    min_weight_g: float
    max_weight_g: float
    shipping_cost_jpy: float
    shipping_method: str


def load_shipping_rates(path: Path) -> list[ShippingRate]:
    if not path.exists():
        raise FileNotFoundError(
            f"送料テーブルが見つかりません: {path}\n"
            "data/shipping_rates.csv を用意してください。"
        )
    rates: list[ShippingRate] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rates.append(
                ShippingRate(
                    market=row["market"].strip().upper(),
                    min_weight_g=float(row["min_weight_g"]),
                    max_weight_g=float(row["max_weight_g"]),
                    shipping_cost_jpy=float(row["shipping_cost_jpy"]),
                    shipping_method=row.get("shipping_method", "").strip(),
                )
            )
    return rates


def find_shipping_cost(
    rates: list[ShippingRate], market: str, shipping_weight_g: float
) -> Optional[ShippingRate]:
    market = market.strip().upper()
    for r in rates:
        if r.market == market and r.min_weight_g <= shipping_weight_g <= r.max_weight_g:
            return r
    return None


@dataclass
class ProfitResult:
    status: str  # "OK" / "SHIPPING_RATE_MISSING" / "DATA_INCOMPLETE" / "CONFIG_MISSING"
    profit_jpy: Optional[float] = None
    detail: str = ""


def calculate_profit(
    *,
    market: str,  # "SG" or "MY"
    sell_price_local: Optional[float],
    purchase_price_jpy: Optional[float],
    shipping_weight_g: Optional[float],
    rates: list[ShippingRate],
    settings: Settings,
) -> ProfitResult:
    market = market.strip().upper()

    if not settings.is_complete:
        return ProfitResult(
            status="CONFIG_MISSING",
            detail=f".envの必須設定が未入力です: {settings.missing_summary()}",
        )

    if purchase_price_jpy is None or sell_price_local is None:
        return ProfitResult(status="DATA_INCOMPLETE", detail="仕入価格または販売価格が未入力です")

    if shipping_weight_g is None:
        return ProfitResult(status="DATA_INCOMPLETE", detail="shipping_weight_gが未入力です")

    rate = find_shipping_cost(rates, market, shipping_weight_g)
    if rate is None:
        return ProfitResult(
            status="SHIPPING_RATE_MISSING",
            detail=f"{market}向け送料が見つかりません(重量={shipping_weight_g}g)",
        )

    if market == "SG":
        exchange_rate = settings.exchange_rate_sgd
        fee_rate = settings.shopee_fee_rate_sg
    elif market == "MY":
        exchange_rate = settings.exchange_rate_myr
        fee_rate = settings.shopee_fee_rate_my
    else:
        return ProfitResult(status="DATA_INCOMPLETE", detail=f"未対応のmarketです: {market}")

    sell_price_jpy = sell_price_local * exchange_rate
    shopee_fee = sell_price_jpy * fee_rate
    payment_fee = sell_price_jpy * settings.payment_fee_rate
    other_costs = settings.other_costs_jpy

    profit = (
        sell_price_jpy
        - purchase_price_jpy
        - rate.shipping_cost_jpy
        - shopee_fee
        - payment_fee
        - other_costs
    )

    return ProfitResult(
        status="OK",
        profit_jpy=round(profit, 1),
        detail=(
            f"sell_price_jpy={sell_price_jpy:.1f}, shipping={rate.shipping_cost_jpy}, "
            f"shopee_fee={shopee_fee:.1f}, payment_fee={payment_fee:.1f}, other={other_costs}"
        ),
    )
