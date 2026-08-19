"""Minimal Shopee Open Platform v2 client used by the management app."""

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

    def exchange_authorization_code(self, code: str, shop_id: int) -> dict[str, Any]:
        path = "/api/v2/auth/token/get"
        timestamp = int(time.time())
        partner_id = self.credentials.partner_id
        sign = self._sign(f"{partner_id}{path}{timestamp}")
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params={"partner_id": partner_id, "timestamp": timestamp, "sign": sign},
"""Minimal Shopee Open Platform v2 client used by the management app."""

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

    def exchange_authorization_code(self, code: str, shop_id: int) -> dict[str, Any]:
        path = "/api/v2/auth/token/get"
        timestamp = int(time.time())
        partner_id = self.credentials.partner_id
        sign = self._sign(f"{partner_id}{path}{timestamp}")
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params={"partner_id": partner_id, "timestamp": timestamp, "sign": sign},"""Minimal Shopee Open Platform v2 client used by the management app."""

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

    def exchange_authorization_code(self, code: str, shop_id: int) -> dict[str, Any]:
        path = "/api/v2/auth/token/get"
        timestamp = int(time.time())
        partner_id = self.credentials.partner_id
        sign = self._sign(f"{partner_id}{path}{timestamp}")
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params={"partner_id": partner_id, "timestamp": timestamp, "sign": sign},
            json={"code": code, "shop_id": shop_id, "partner_id": partner_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload

    def add_item_unlisted(
        self, access_token: str, shop_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Create one Shopee item, refusing any payload that could go live."""
        if payload.get("item_status") != "UNLIST":
            raise ValueError("Safety check: new API items must use item_status=UNLIST")
        path = "/api/v2/product/add_item"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise ShopeeAPIError(result.get("message") or result["error"])
        return result.get("response", result)

    def recommend_category(
        self, access_token: str, shop_id: int, item_name: str
    ) -> dict[str, Any]:
        path = "/api/v2/product/category_recommend"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params={
                **self._shop_params(path, access_token, shop_id),
                "item_name": item_name,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload.get("response", payload)

    def get_logistics_channels(
        self, access_token: str, shop_id: int
    ) -> list[dict[str, Any]]:
        path = "/api/v2/logistics/get_channel_list"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        return body.get("logistics_channel_list", [])

    def upload_image_bytes(
        self,
        access_token: str,
        shop_id: int,
        image_bytes: bytes,
        filename: str = "product.jpg",
    ) -> str:
        path = "/api/v2/media_space/upload_image"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            files={"image": (filename, image_bytes, "image/jpeg")},
            timeout=max(self.timeout, 45),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        image_info = body.get("image_info", body)
        image_id = image_info.get("image_id")
        if not image_id:
            raise ShopeeAPIError("Shopee画像IDを取得できませんでした")
        return str(image_id)
            json={"code": code, "shop_id": shop_id, "partner_id": partner_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload

    def add_item_unlisted(
        self, access_token: str, shop_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Create one Shopee item, refusing any payload that could go live."""
        if payload.get("item_status") != "UNLIST":
            raise ValueError("Safety check: new API items must use item_status=UNLIST")
        path = "/api/v2/product/add_item"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise ShopeeAPIError(result.get("message") or result["error"])
        return result.get("response", result)

    def recommend_category(
        self, access_token: str, shop_id: int, item_name: str
    ) -> dict[str, Any]:
        path = "/api/v2/product/category_recommend"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params={
                **self._shop_params(path, access_token, shop_id),
                "item_name": item_name,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload.get("response", payload)

    def get_logistics_channels(
        self, access_token: str, shop_id: int
    ) -> list[dict[str, Any]]:
        path = "/api/v2/logistics/get_channel_list"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        return body.get("logistics_channel_list", [])

    def upload_image_bytes(
        self,
        access_token: str,
        shop_id: int,
        image_bytes: bytes,
        filename: str = "product.jpg",
    ) -> str:
        path = "/api/v2/media_space/upload_image"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            files={"image": (filename, image_bytes, "image/jpeg")},
            timeout=max(self.timeout, 45),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        image_info = body.get("image_info", body)
        image_id = image_info.get("image_id")
        if not image_id:
            raise ShopeeAPIError("Shopee画像IDを取得できませんでした")
        return str(image_id)
            json={"code": code, "shop_id": shop_id, "partner_id": partner_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload

    def add_item_unlisted(
        self, access_token: str, shop_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Create one Shopee item, refusing any payload that could go live."""
        if payload.get("item_status") != "UNLIST":
            raise ValueError("Safety check: new API items must use item_status=UNLIST")
        path = "/api/v2/product/add_item"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise ShopeeAPIError(result.get("message") or result["error"])
        return result.get("response", result)

    def recommend_category(
        self, access_token: str, shop_id: int, item_name: str
    ) -> dict[str, Any]:
        path = "/api/v2/product/category_recommend"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params={
                **self._shop_params(path, access_token, shop_id),
                "item_name": item_name,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        return payload.get("response", payload)

    def get_logistics_channels(
        self, access_token: str, shop_id: int
    ) -> list[dict[str, Any]]:
        path = "/api/v2/logistics/get_channel_list"
        response = requests.get(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        return body.get("logistics_channel_list", [])

    def upload_image_bytes(
        self,
        access_token: str,
        shop_id: int,
        image_bytes: bytes,
        filename: str = "product.jpg",
    ) -> str:
        path = "/api/v2/media_space/upload_image"
        response = requests.post(
            f"{self.credentials.base_url}{path}",
            params=self._shop_params(path, access_token, shop_id),
            files={"image": (filename, image_bytes, "image/jpeg")},
            timeout=max(self.timeout, 45),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ShopeeAPIError(payload.get("message") or payload["error"])
        body = payload.get("response", payload)
        image_info = body.get("image_info", body)
        image_id = image_info.get("image_id")
        if not image_id:
            raise ShopeeAPIError("Shopee画像IDを取得できませんでした")
        return str(image_id)
