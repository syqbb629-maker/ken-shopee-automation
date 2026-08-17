"""
pipeline.py
-------------
V2仕様23の実装(dry-run対応の共通パイプライン)。

商品検査 -> 画像検査 -> 在庫確認 -> 利益計算 -> READY判定
-> SG Excel生成 -> MY Excel生成 -> ログ保存

CLI(app.py --dry-run)とStreamlit管理画面の両方から呼び出せるよう
共通関数として実装している。dry_run=True の場合はShopeeへの送信(実際の
出品API呼び出し)は一切行わない(そもそも本V2には自動出品APIは実装して
いないため、常にローカルファイル生成までが処理範囲)。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import config
from .product_master import load_product_master, save_product_master
from .profit_calculator import load_shipping_rates
from .product_validator import validate_product
from .description_generator import generate_description
from .inventory_checker import check_source_stock
from .shopee_excel_generator import generate_shopee_excel, TemplateNotFoundError

logger = logging.getLogger("shopee_dropship")


def setup_logging() -> None:
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = config.LOGS_DIR / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


@dataclass
class PipelineResult:
    total_rows: int = 0
    ready_count: int = 0
    status_counts: dict = field(default_factory=dict)
    sg_excel_written: int | None = None
    my_excel_written: int | None = None
    sg_excel_error: str | None = None
    my_excel_error: str | None = None
    settings_missing: list = field(default_factory=list)


def run_pipeline(
    *,
    product_master_path: Path | None = None,
    refresh_inventory: bool = True,
    dry_run: bool = True,
) -> PipelineResult:
    setup_logging()
    logger.info("=== パイプライン開始 (dry_run=%s) ===", dry_run)

    product_master_path = product_master_path or config.PRODUCT_MASTER_PATH
    df = load_product_master(product_master_path)
    shipping_rates = load_shipping_rates(config.SHIPPING_RATES_PATH)
    settings = config.load_settings()

    if not settings.is_complete:
        logger.warning(".envの必須設定が未入力です: %s", settings.missing_summary())

    status_counts: dict[str, int] = {}

    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        # 在庫確認(URL到達性 + 既存値の尊重)
        if refresh_inventory:
            stock_status, checked_at = check_source_stock(
                row_dict.get("source_url", ""), row_dict.get("source_stock_status", "")
            )
            row_dict["source_stock_status"] = stock_status
            row_dict["source_checked_at"] = checked_at
            df.at[idx, "source_stock_status"] = stock_status
            df.at[idx, "source_checked_at"] = checked_at

        # 説明文生成(既存の説明文が空の場合のみ自動生成し、事実のみ使用)
        if not (row_dict.get("description_en", "") or "").strip():
            desc_result = generate_description(row_dict)
            row_dict["description_en"] = desc_result.text
            df.at[idx, "description_en"] = desc_result.text
            for w in desc_result.warnings:
                logger.warning("item_id=%s 説明文警告: %s", row_dict.get("item_id"), w)

        result = validate_product(row_dict, shipping_rates=shipping_rates, settings=settings)

        df.at[idx, "listing_status"] = str(result.listing_status)
        if result.profit_sg is not None and result.profit_sg.profit_jpy is not None:
            df.at[idx, "profit_sg_jpy"] = str(result.profit_sg.profit_jpy)
        if result.profit_my is not None and result.profit_my.profit_jpy is not None:
            df.at[idx, "profit_my_jpy"] = str(result.profit_my.profit_jpy)

        status_counts[result.listing_status] = status_counts.get(result.listing_status, 0) + 1
        logger.info(
            "item_id=%s listing_status=%s reasons=%s",
            row_dict.get("item_id"), result.listing_status, "; ".join(result.reasons),
        )

    save_product_master(df, product_master_path)

    ready_df = df[df["listing_status"] == config.ListingStatus.READY_TO_LIST]

    pipeline_result = PipelineResult(
        total_rows=len(df),
        ready_count=len(ready_df),
        status_counts=status_counts,
        settings_missing=settings.missing_fields,
    )

    # SG Excel生成
    try:
        written = generate_shopee_excel(
            ready_df, config.SG_TEMPLATE_PATH, config.SG_OUTPUT_PATH, market="SG"
        )
        pipeline_result.sg_excel_written = written
        logger.info("SG Excel生成完了: %d件 -> %s", written, config.SG_OUTPUT_PATH)
    except TemplateNotFoundError as e:
        pipeline_result.sg_excel_error = str(e)
        logger.warning("SG Excel生成スキップ: %s", e)

    # MY Excel生成
    try:
        written = generate_shopee_excel(
            ready_df, config.MY_TEMPLATE_PATH, config.MY_OUTPUT_PATH, market="MY"
        )
        pipeline_result.my_excel_written = written
        logger.info("MY Excel生成完了: %d件 -> %s", written, config.MY_OUTPUT_PATH)
    except TemplateNotFoundError as e:
        pipeline_result.my_excel_error = str(e)
        logger.warning("MY Excel生成スキップ: %s", e)

    logger.info("=== パイプライン終了 ===")
    return pipeline_result
