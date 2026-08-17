"""
config.py
----------
.env から為替レート・Shopee手数料などの運用パラメータを読み込む。
コード内に固定値をハードコードしない方針(V2で修正した問題点の一つ)。

必須パラメータが未設定/不正な場合、READY_TO_LIST判定を行わないため
CONFIG_MISSING を報告する仕組みを提供する。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

PRODUCT_MASTER_PATH = DATA_DIR / "product_master.xlsx"
SHIPPING_RATES_PATH = DATA_DIR / "shipping_rates.csv"

SG_TEMPLATE_PATH = TEMPLATES_DIR / "shopee_sg_template.xlsx"
MY_TEMPLATE_PATH = TEMPLATES_DIR / "shopee_my_template.xlsx"

SG_OUTPUT_PATH = OUTPUT_DIR / "shopee_sg_ready.xlsx"
MY_OUTPUT_PATH = OUTPUT_DIR / "shopee_my_ready.xlsx"

DEFAULT_STOCK = 2  # 無在庫販売のため、Shopee上の在庫数は少数固定


def _get_float(name: str) -> Optional[float]:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


@dataclass
class Settings:
    exchange_rate_sgd: Optional[float] = None
    exchange_rate_myr: Optional[float] = None
    shopee_fee_rate_sg: Optional[float] = None
    shopee_fee_rate_my: Optional[float] = None
    payment_fee_rate: Optional[float] = None
    other_costs_jpy: Optional[float] = None

    missing_fields: list = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.missing_fields) == 0

    def missing_summary(self) -> str:
        return ", ".join(self.missing_fields) if self.missing_fields else ""


def load_settings(env_path: Optional[Path] = None) -> Settings:
    """.env を読み込み、Settings を返す。未設定項目は missing_fields に記録する。"""
    if env_path is None:
        env_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    s = Settings(
        exchange_rate_sgd=_get_float("EXCHANGE_RATE_SGD"),
        exchange_rate_myr=_get_float("EXCHANGE_RATE_MYR"),
        shopee_fee_rate_sg=_get_float("SHOPEE_FEE_RATE_SG"),
        shopee_fee_rate_my=_get_float("SHOPEE_FEE_RATE_MY"),
        payment_fee_rate=_get_float("PAYMENT_FEE_RATE"),
        other_costs_jpy=_get_float("OTHER_COSTS"),
    )

    field_names = {
        "exchange_rate_sgd": "EXCHANGE_RATE_SGD",
        "exchange_rate_myr": "EXCHANGE_RATE_MYR",
        "shopee_fee_rate_sg": "SHOPEE_FEE_RATE_SG",
        "shopee_fee_rate_my": "SHOPEE_FEE_RATE_MY",
        "payment_fee_rate": "PAYMENT_FEE_RATE",
        "other_costs_jpy": "OTHER_COSTS",
    }
    for attr, env_name in field_names.items():
        if getattr(s, attr) is None:
            s.missing_fields.append(env_name)

    return s


# listing_status で使う定数(V2仕様18)
class ListingStatus:
    READY_TO_LIST = "READY_TO_LIST"
    IMAGE_REVIEW_REQUIRED = "IMAGE_REVIEW_REQUIRED"
    REGULATION_REVIEW_REQUIRED = "REGULATION_REVIEW_REQUIRED"
    WEIGHT_REVIEW_REQUIRED = "WEIGHT_REVIEW_REQUIRED"
    SHIPPING_REVIEW_REQUIRED = "SHIPPING_REVIEW_REQUIRED"
    SHIPPING_RATE_MISSING = "SHIPPING_RATE_MISSING"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW_PROFIT = "LOW_PROFIT"
    DISCONTINUED = "DISCONTINUED"
    DATA_INCOMPLETE = "DATA_INCOMPLETE"
    STOP_CANDIDATE = "STOP_CANDIDATE"
    CONFIG_MISSING = "CONFIG_MISSING"


class ImageLicenseStatus:
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class ImageMatchStatus:
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class StockStatus:
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"


class WeightSource:
    MANUFACTURER = "manufacturer"
    SUPPLIER = "supplier"
    MANUAL = "manual"
    ESTIMATED = "estimated"
