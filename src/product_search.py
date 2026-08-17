"""
product_search.py
--------------------
V2仕様1・29の実装。

商品候補の取得元(杏林堂/ウエルシア/スギ薬局/マツモトキヨシ等)は
サイトごとに規約・構造が異なるため、本モジュールは「候補取得の入り口」を
共通インターフェースとして提供し、実際のサイト別スクレイパーは
プラガブルに追加できる設計にしている。

現時点ではネットワークアクセスが制限された環境での動作を優先し、
data/product_master.xlsx に人手/外部ツールで登録された候補行を
「新規候補(listing_status未設定)」として読み込む方式を既定実装とする。

段階的検証(仕様29): 5商品 → 20商品 → 100商品
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .product_master import load_product_master

STAGE_LIMITS = [5, 20, 100]


def get_candidates(product_master_path: Path, stage: int = 1) -> pd.DataFrame:
    """商品マスターから、まだ検査(listing_status未設定)の候補を
    段階的検証の上限件数まで取得する。

    stage: 1 -> 5件, 2 -> 20件, 3 -> 100件
    """
    if stage < 1 or stage > len(STAGE_LIMITS):
        raise ValueError(f"stageは1〜{len(STAGE_LIMITS)}の範囲で指定してください")

    limit = STAGE_LIMITS[stage - 1]
    df = load_product_master(product_master_path)
    candidates = df[df["listing_status"].str.strip() == ""]
    return candidates.head(limit)
