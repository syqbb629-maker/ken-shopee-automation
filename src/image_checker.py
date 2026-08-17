"""
image_checker.py
------------------
V2仕様8・9・10 の実装。

- 画像の実在確認(ローカル/URL)
- 画像利用許諾(image_license_status)の管理
- 商品と画像の一致確認(image_match_status)の管理

重要: このモジュールは「画像が本当に使ってよいか」を自動で判定しません。
ネット上から拾った画像を無条件にAPPROVEDにする処理は行いません。
image_license_status / image_match_status は商品マスターに記録された値
(人が確認して入力した値、またはNETSEA等の転載可フラグを反映した値)を
そのまま尊重し、このモジュールは「その値が本当に成立する状態か」
(=画像ファイルが実在し壊れていないか)だけを検証します。
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, UnidentifiedImageError

from config import ImageLicenseStatus, ImageMatchStatus

REQUEST_TIMEOUT = 10


@dataclass
class ImageCheckResult:
    file_ok: bool
    license_ok: bool
    match_ok: bool
    reason: str

    @property
    def passes(self) -> bool:
        return self.file_ok and self.license_ok and self.match_ok


def _check_local_image(path_str: str) -> tuple[bool, str]:
    p = Path(path_str)
    if not p.exists():
        return False, f"ローカル画像が存在しません: {path_str}"
    try:
        with Image.open(p) as img:
            img.verify()
        return True, ""
    except (UnidentifiedImageError, OSError) as e:
        return False, f"ローカル画像が壊れています: {path_str} ({e})"


def _check_remote_image(url: str) -> tuple[bool, str]:
    if not url:
        return False, "画像URLが空です"
    try:
        resp = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code >= 400 or "image" not in resp.headers.get("Content-Type", ""):
            # HEADが使えないサーバー向けにGETで再確認
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        if resp.status_code >= 400:
            return False, f"画像URLの取得に失敗しました(HTTP {resp.status_code}): {url}"
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type:
            return False, f"画像ではないContent-Typeです({content_type}): {url}"
        # 実データを取得して破損チェック
        r2 = requests.get(url, timeout=REQUEST_TIMEOUT)
        Image.open(io.BytesIO(r2.content)).verify()
        return True, ""
    except requests.RequestException as e:
        return False, f"画像URLへの接続に失敗しました: {url} ({e})"
    except (UnidentifiedImageError, OSError) as e:
        return False, f"画像データが壊れています: {url} ({e})"


def check_image_file(image_main_local: str, image_main_url: str) -> tuple[bool, str]:
    """メイン画像ファイルが実在し破損していないかを確認する(V2仕様10)。
    ローカルパスが指定されていればそちらを優先確認し、
    なければURLを確認する。どちらも無ければ IMAGE_REVIEW_REQUIRED 相当。
    """
    image_main_local = (image_main_local or "").strip()
    image_main_url = (image_main_url or "").strip()

    if not image_main_local and not image_main_url:
        return False, "画像が指定されていません(image_main_local / image_main_url とも空)"

    if image_main_local:
        ok, reason = _check_local_image(image_main_local)
        if ok:
            return True, ""
        # ローカルが無ければURLでフォールバック確認
        if image_main_url:
            ok2, reason2 = _check_remote_image(image_main_url)
            if ok2:
                return True, ""
            return False, f"{reason} / {reason2}"
        return False, reason

    return _check_remote_image(image_main_url)


def evaluate_image(row: dict) -> ImageCheckResult:
    """商品マスター1行分の画像情報を評価する。"""
    file_ok, file_reason = check_image_file(
        row.get("image_main_local", ""), row.get("image_main_url", "")
    )

    license_status = (row.get("image_license_status", "") or "").strip()
    match_status = (row.get("image_match_status", "") or "").strip()

    license_ok = license_status == ImageLicenseStatus.APPROVED
    match_ok = match_status == ImageMatchStatus.MATCHED

    reasons = []
    if not file_ok:
        reasons.append(file_reason)
    if not license_ok:
        reasons.append(f"image_license_status={license_status or '未設定'}(APPROVED以外)")
    if not match_ok:
        reasons.append(f"image_match_status={match_status or '未設定'}(MATCHED以外)")

    return ImageCheckResult(
        file_ok=file_ok,
        license_ok=license_ok,
        match_ok=match_ok,
        reason="; ".join(reasons) if reasons else "OK",
    )
