"""Minimal Shopee Open Platform v2 client used for connection checks."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests

DEFAULT_BASE_URL = "https://partner.shopeemobile.com"


class ShopeeAPIError(RuntimeError):
    """Raised when Shopee returns an API error."""


@dataclass(frozen=True)
class ShopeeCredentials:
    partner_id: int
    partner_key: str
    redirect_url: str
    base_url: str = DEFAULT_BASE_URL


class ShopeeClient:
    def __init__(self, credentials: ShopeeCredentials, timeout: int = 20) -> None:
        self.credentials = credentials
        self.timeout = timeout

    def _sign(self, base_string: str) -> str:
        return hmac.new(
            self.credentials.partner_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def authorization_url(self) -> str:
        path = "/api/v2/shop/auth_partner"
        timestamp = int(time.time())
        partner_id = self.credentials.partner_id
        sign = self._sign(f"{partner_id}{path}{timestamp}")
        query = urlencode({
            "partner_id": partner_id,
            "timestamp": timestamp,
            "sign": sign,
            "redirect": self.credentials.redirect_url,
        })
        return f"{self.credentials.base_url}{path}?{query}"

    def _shop_params(self, path: str, access_token: str, shop_id: int) -> dict[str, Any]:
        timestamp = int(time.time())
        partner_id = self.credentials.partner_id
        sign = self._sign(f"{partner_id}{path}{timestamp}{access_token}{shop_id}")
        return {
            "partner_id": partner_id,
            "timestamp": timestamp,
            "access_token": access_token,
            "shop_id": shop_id,
            "sign": sign,
        }

    def get_shop_info(self, access_token: str, shop_id: int) -> dict[str, Any]:
        path = "/api/v2/shop/get_shop_info"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload.get("response", payload)

