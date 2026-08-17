"""
product_master.py
------------------
data/product_master.xlsx の読み込み・保存ユーティリティ。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import PRODUCT_MASTER_COLUMNS


def load_product_master(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"商品マスターが見つかりません: {path}\n"
            "data/product_master.xlsx を用意してください。"
        )
    df = pd.read_excel(path, dtype=str)
    # 欠けている列があれば空文字で補う(古いマスターとの互換用)
    for col in PRODUCT_MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[PRODUCT_MASTER_COLUMNS]
    return df.fillna("")


def save_product_master(df: pd.DataFrame, path: Path) -> None:
    df = df[PRODUCT_MASTER_COLUMNS]
    df.to_excel(path, index=False)
