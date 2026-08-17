"""
inventory_checker.py
----------------------
V2仕様12の実装。

仕入先(ドラッグストアのECサイト等)の在庫状態を確認する。
実際のサイトごとのスクレイピングは対象サイトの利用規約確認が必要なため、
ここでは「URLへの到達性確認」までを共通処理として提供し、
実際の在庫判定ロジックはサイトごとにプラガブルに追加できる設計にしている。

到達性確認だけでは在庫の有無は断定できないため、判定できない場合は
必ず UNKNOWN を返す(仕様どおり、UNKNOWNはREADY_TO_LISTにしない)。
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from config import StockStatus

REQUEST_TIMEOUT = 10


def check_source_stock(source_url: str, declared_status: str = "") -> tuple[str, str]:
    """仕入先の在庫状態を確認する。

    declared_status: 商品マスターに人手/外部ツールで記録済みの在庫状態
                      (IN_STOCK/LOW_STOCK/OUT_OF_STOCK/UNKNOWN)があれば
                      それを尊重しつつ、URLの到達性だけ確認する。
    戻り値: (status, checked_at_iso)
    """
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_url = (source_url or "").strip()
    declared_status = (declared_status or "").strip().upper()

    valid_statuses = {
        StockStatus.IN_STOCK,
        StockStatus.LOW_STOCK,
        StockStatus.OUT_OF_STOCK,
        StockStatus.UNKNOWN,
    }

    if not source_url:
        return StockStatus.UNKNOWN, checked_at

    try:
        resp = requests.head(source_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        reachable = resp.status_code < 400
    except requests.RequestException:
        reachable = False

    if not reachable:
        # 通信が一時的に不安定なだけで在庫状態自体が変わったとは限らないため、
        # 既に人手/外部ツールで確認済みの値があればそれを保持する。
        # 何も記録が無い場合のみ安全側に倒してUNKNOWNとする。
        if declared_status in valid_statuses:
            return declared_status, checked_at
        return StockStatus.UNKNOWN, checked_at

    if declared_status in valid_statuses:
        return declared_status, checked_at

    # 到達はできたが在庫状態を判定する具体的なロジックが無い場合は
    # 安全側に倒してUNKNOWNとする(誤ってIN_STOCK扱いにしない)
    return StockStatus.UNKNOWN, checked_at
