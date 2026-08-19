"""
app.py
-------
実行方法:

  CLI(dry-run。Shopeeへは何も送信しません):
      python app.py --dry-run

  Streamlit管理画面:
      streamlit run app.py
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import requests
import streamlit as st
import streamlit_authenticator as stauth

import config
from src.pipeline import run_pipeline
from src.product_master import load_product_master, save_product_master
from src.shopee_api import ShopeeAPIError, ShopeeClient, ShopeeCredentials
from src.shopee_listing import build_sg_unlisted_payload


FIRST_SG_ITEM = {
    "item_id": "NETSEA-4513574029347",
    "product_name_jp": "熊野油脂 麗白ハトムギ泡洗顔 本体 160ml",
    "product_name_en": "Kumano Reihaku Hatomugi Foaming Facial Wash 160ml Japan",
    "description_en": (
        "Kumano Reihaku Hatomugi Foaming Facial Wash 160ml. Fine cushiony foam "
        "gently cleanses the skin. Formulated with Hatomugi (Job's tears) seed "
        "extract and hyaluronic acid as moisturizing ingredients. Pump bottle. "
        "Made in Japan. JAN: 4513574029347. Package design may change without notice."
    ),
    "brand": "Kumano Yushi",
    "source_url": "https://www.netsea.jp/shop/939589/4513574029347",
    "image_url": "https://img03.netsea.jp/ex35/20260210/5/23785535_0.jpg",
    "sg_price": 19.90,
    "shipping_weight_g": 250,
    "stock": 1,
    "package_height_cm": 18,
    "package_length_cm": 11,
    "package_width_cm": 7,
    "sku_sg": "4513574029347",
    "listing_status": "READY_TO_LIST",
}


def _secret(name: str, default: str = "") -> str:
    """Read a Streamlit secret first, then an environment variable."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = os.getenv(name, default)
    return str(value).strip() if value is not None else default


def _render_shopee_connection() -> None:
    st.subheader("🔌 Shopee API接続")
    required = ("SHOPEE_PARTNER_ID", "SHOPEE_PARTNER_KEY", "SHOPEE_REDIRECT_URL")
    missing = [name for name in required if not _secret(name)]
    if missing:
        st.warning("API接続設定が未完了です（秘密情報は画面には表示しません）。")
        st.caption("未設定: " + ", ".join(missing))
        return

    try:
        client = ShopeeClient(ShopeeCredentials(
            partner_id=int(_secret("SHOPEE_PARTNER_ID")),
            partner_key=_secret("SHOPEE_PARTNER_KEY"),
            redirect_url=_secret("SHOPEE_REDIRECT_URL"),
            base_url=_secret("SHOPEE_BASE_URL", "https://partner.shopeemobile.com"),
        ))
    except ValueError:
        st.error("SHOPEE_PARTNER_ID の形式が正しくありません。")
        return

    st.link_button("SG/MY店舗をShopeeで認証", client.authorization_url())

    auth_code = st.query_params.get("code")
    auth_shop_id = st.query_params.get("shop_id")
    if auth_code and auth_shop_id:
        st.success(f"Shopeeから認証結果を受信しました（Shop ID: {auth_shop_id}）")
        if st.button("認証コードをAccess Tokenへ交換", type="primary"):
            try:
                token_data = client.exchange_authorization_code(auth_code, int(auth_shop_id))
                st.session_state["new_shopee_shop_id"] = str(auth_shop_id)
                st.session_state["new_shopee_access_token"] = token_data["access_token"]
                st.session_state["new_shopee_refresh_token"] = token_data.get("refresh_token", "")
                st.query_params.clear()
                st.rerun()
            except (KeyError, ValueError, requests.RequestException, ShopeeAPIError) as exc:
                st.error(f"トークン取得失敗: {exc}")

    if st.session_state.get("new_shopee_access_token"):
        st.success("Access Tokenを取得しました。秘密設定へ保存するまで画面を閉じないでください。")
        st.text_input("認証済みShop ID", value=st.session_state["new_shopee_shop_id"], disabled=True)
        st.text_input("新しいAccess Token", value=st.session_state["new_shopee_access_token"], type="password", disabled=True)
        st.text_input("新しいRefresh Token", value=st.session_state.get("new_shopee_refresh_token", ""), type="password", disabled=True)
    cols = st.columns(2)
    for col, market in zip(cols, ("SG", "MY")):
        shop_id_text = _secret(f"SHOPEE_{market}_SHOP_ID")
        access_token = _secret(f"SHOPEE_{market}_ACCESS_TOKEN")
        with col:
            st.markdown(f"**{market}店舗**")
            if not shop_id_text or not access_token:
                st.info("未接続（Shop IDまたはAccess Tokenが未設定）")
                continue
            if st.button(f"{market} 接続テスト", key=f"test_{market.lower()}_connection"):
                try:
                    info = client.get_shop_info(access_token, int(shop_id_text))
                    shop_name = info.get("shop_name") or info.get("shop_id") or shop_id_text
                    st.success(f"接続成功: {shop_name}")
                except (ValueError, requests.RequestException, ShopeeAPIError) as exc:
                    st.error(f"接続失敗: {exc}")


def _sg_client() -> tuple[ShopeeClient, str, int]:
    client = ShopeeClient(ShopeeCredentials(
        partner_id=int(_secret("SHOPEE_PARTNER_ID")),
        partner_key=_secret("SHOPEE_PARTNER_KEY"),
        redirect_url=_secret("SHOPEE_REDIRECT_URL"),
        base_url=_secret("SHOPEE_BASE_URL", "https://partner.shopeemobile.com"),
    ))
    return client, _secret("SHOPEE_SG_ACCESS_TOKEN"), int(_secret("SHOPEE_SG_SHOP_ID"))


def _render_first_sg_item() -> None:
    st.subheader("🇸🇬 SG 最初の1点")
    st.image(FIRST_SG_ITEM["image_url"], width=220)
    st.write(FIRST_SG_ITEM["product_name_en"])
    st.write(f"価格: {FIRST_SG_ITEM['sg_price']:.2f} SGD / 在庫: 1 / 非公開登録")
    st.caption("登録準備では画像・推奨カテゴリ・利用可能な配送方法をShopee APIで取得します。")

    if st.button("1. Shopee登録準備", key="prepare_first_sg"):
        try:
            client, token, shop_id = _sg_client()
            image_response = requests.get(FIRST_SG_ITEM["image_url"], timeout=30)
            image_response.raise_for_status()
            image_id = client.upload_image_bytes(token, shop_id, image_response.content)
            category = client.recommend_category(token, shop_id, FIRST_SG_ITEM["product_name_en"])
            category_id = int(category.get("category_id") or 0)
            channels = client.get_logistics_channels(token, shop_id)
            enabled = [c for c in channels if c.get("enabled") is not False]
            if not category_id:
                raise ShopeeAPIError("推奨カテゴリIDを取得できませんでした")
            if not enabled:
                raise ShopeeAPIError("利用可能な配送方法がありません")
            row = dict(FIRST_SG_ITEM)
            row["shopee_image_id"] = image_id
            row["shopee_sg_category_id"] = category_id
            row["shopee_sg_logistic_id"] = int(enabled[0]["logistics_channel_id"])
            preflight = build_sg_unlisted_payload(row)
            if not preflight.ready:
                raise ShopeeAPIError(" / ".join(preflight.blockers))
            st.session_state["first_sg_payload"] = preflight.payload
            st.session_state["first_sg_channel"] = enabled[0].get("logistics_channel_name", "")
            st.success("準備完了。下の内容を確認してください。")
        except (ValueError, KeyError, requests.RequestException, ShopeeAPIError) as exc:
            st.error(f"登録準備に失敗しました: {exc}")

    payload = st.session_state.get("first_sg_payload")
    if payload:
        st.write(f"カテゴリID: {payload['category_id']}")
        st.write(f"配送方法: {st.session_state.get('first_sg_channel', '')}")
        st.warning("次のボタンを押すと、Shopee SG店に非公開の商品が1件作成されます。")
        if st.button("2. Shopee SGへ非公開で登録", type="primary", key="create_first_sg"):
            try:
                client, token, shop_id = _sg_client()
                result = client.add_item_unlisted(token, shop_id, payload)
                st.session_state.pop("first_sg_payload", None)
                st.success(f"非公開登録が完了しました。Shopee Item ID: {result.get('item_id', '取得中')}")
            except (ValueError, requests.RequestException, ShopeeAPIError) as exc:
                st.error(f"Shopee登録に失敗しました: {exc}")


# ----------------------------------------------------------------------
# CLI (dry-run)
# ----------------------------------------------------------------------
def run_dry_run() -> None:
    result = run_pipeline(dry_run=True, refresh_inventory=True)

    print("\n=== dry-run 結果 ===")
    print(f"検査商品数: {result.total_rows}")
    print(f"READY_TO_LIST件数: {result.ready_count}")
    print("ステータス内訳:")
    for status, count in sorted(result.status_counts.items()):
        print(f"  {status}: {count}")

    if result.settings_missing:
        print(f"\n[警告] .envの未設定項目: {', '.join(result.settings_missing)}")
        print("      .env.example を参考に .env を作成/編集してください。")

    if result.sg_excel_written is not None:
        print(f"\nSG Excel生成: {result.sg_excel_written}件 -> {config.SG_OUTPUT_PATH}")
    else:
        print(f"\nSG Excel生成: スキップ({result.sg_excel_error})")

    if result.my_excel_written is not None:
        print(f"MY Excel生成: {result.my_excel_written}件 -> {config.MY_OUTPUT_PATH}")
    else:
        print(f"MY Excel生成: スキップ({result.my_excel_error})")

    print(f"\nログ: {config.LOGS_DIR / 'app.log'}")


# ----------------------------------------------------------------------
# Streamlit 管理画面
# ----------------------------------------------------------------------
def run_streamlit_app() -> None:
    st.set_page_config(page_title="Shopee ドラッグストア無在庫販売 管理画面", layout="wide")

    # 30-day signed login cookie. Credentials and signing key stay in Secrets.
    review_user = _secret("REVIEW_USERNAME")
    review_password = _secret("REVIEW_PASSWORD")
    cookie_key = _secret("AUTH_COOKIE_KEY")
    if not review_user or not review_password or not cookie_key:
        st.error("Login is not configured. Set REVIEW_USERNAME, REVIEW_PASSWORD and AUTH_COOKIE_KEY.")
        st.stop()

    credentials = {
        "usernames": {
            review_user: {
                "email": "",
                "first_name": "Ken",
                "last_name": "Asano",
                "password": review_password,
            }
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        "ken_shopee_login",
        cookie_key,
        30,
    )
    authenticator.login()
    if st.session_state.get("authentication_status") is False:
        st.error("Invalid username or password")
        st.stop()
    if st.session_state.get("authentication_status") is not True:
        st.stop()

    st.title("🧴 Shopee ドラッグストア無在庫販売 管理画面 (V2)")

    authenticator.logout("Sign out", "main")

    _render_shopee_connection()
    st.divider()

    if not config.PRODUCT_MASTER_PATH.exists():
        st.error(f"商品マスターが見つかりません: {config.PRODUCT_MASTER_PATH}")
        return

    df = load_product_master(config.PRODUCT_MASTER_PATH)

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    if col_a.button("① 商品検査(全項目)"):
        with st.spinner("検査中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=True)
        st.success(f"完了: READY_TO_LIST {result.ready_count}件 / 全{result.total_rows}件")
        if result.settings_missing:
            st.warning(f".env未設定項目: {', '.join(result.settings_missing)}")
        st.rerun()

    if col_b.button("② 画像確認のみ"):
        with st.spinner("画像確認中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        st.success("画像確認を含む全検査を実行しました")
        st.rerun()

    if col_c.button("③ 利益再計算"):
        with st.spinner("利益再計算中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        st.success("利益を再計算しました")
        st.rerun()

    if col_d.button("④ SG Excel生成"):
        with st.spinner("SG Excel生成中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        if result.sg_excel_written is not None:
            st.success(f"SG Excel生成完了: {result.sg_excel_written}件")
        else:
            st.error(result.sg_excel_error)

    if col_e.button("⑤ MY Excel生成"):
        with st.spinner("MY Excel生成中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        if result.my_excel_written is not None:
            st.success(f"MY Excel生成完了: {result.my_excel_written}件")
        else:
            st.error(result.my_excel_error)

    st.divider()
    st.subheader("商品一覧")

    display_cols = [
        "item_id", "image_main_url", "product_name_jp", "product_name_en",
        "brand", "purchase_price_jpy", "sg_price", "my_price",
        "profit_sg_jpy", "profit_my_jpy", "source_store",
        "source_stock_status", "image_license_status", "image_match_status",
        "listing_status",
    ]
    display_cols = [c for c in display_cols if c in df.columns]

    st.dataframe(
        df[display_cols],
        column_config={
            "image_main_url": st.column_config.ImageColumn("画像", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    _render_first_sg_item()
    st.divider()
    st.subheader("🇸🇬 SG 1件目の自動出品テスト")
    st.caption(
        "安全のため、最初は公開せずUNLIST（非公開）で作成します。"
        "医薬品・サプリ、架空データ、未確認画像は自動的に止めます。"
    )
    ready_rows = df[df["listing_status"] == config.ListingStatus.READY_TO_LIST]
    preview_options = ready_rows["item_id"].astype(str).tolist()
    preview_item_id = st.selectbox(
        "テスト対象item_id", options=[""] + preview_options, key="sg_preview_item_id"
    )
    if preview_item_id:
        preview_row = ready_rows.loc[
            ready_rows["item_id"].astype(str) == preview_item_id
        ].iloc[0].to_dict()
        preflight = build_sg_unlisted_payload(preview_row)
        st.write(f"商品名: {preview_row.get('product_name_en', '')}")
        st.write(f"SG価格: {preview_row.get('sg_price', '')} SGD")
        if preflight.ready:
            st.success("非公開テスト登録の準備が整っています。")
            st.info("実登録ボタンは、商品・カテゴリ・物流・画像IDの最終確認後に有効化します。")
        else:
            st.warning("この商品はまだShopeeへ送りません。次の確認が必要です。")
            for blocker in preflight.blockers:
                st.write(f"・{blocker}")
    elif preview_options:
        st.info("上の欄から1件選ぶと、出品前の安全検査結果を表示します。")
    else:
        st.warning("READY_TO_LISTの商品がありません。先に①商品検査を実行してください。")

    st.divider()
    st.subheader("停止候補にする")
    st.caption(
        "注意: このボタンはShopee上の出品を実際には停止しません。"
        "listing_status を STOP_CANDIDATE に変更するだけです。"
        "実際の出品停止はShopeeセラーセンター(またはSellBridge)で行ってください。"
    )
    item_ids = df["item_id"].tolist()
    target = st.selectbox("対象item_id", options=[""] + item_ids)
    if st.button("停止候補にする", disabled=(target == "")):
        idx = df.index[df["item_id"] == target][0]
        df.at[idx, "listing_status"] = config.ListingStatus.STOP_CANDIDATE
        save_product_master(df, config.PRODUCT_MASTER_PATH)
        st.success(f"item_id={target} を停止候補(STOP_CANDIDATE)にしました")
        st.rerun()


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        run_dry_run()
    else:
        run_streamlit_app()
"""
app.py
-------
実行方法:

  CLI(dry-run。Shopeeへは何も送信しません):
      python app.py --dry-run

  Streamlit管理画面:
      streamlit run app.py
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import requests
import streamlit as st
import streamlit_authenticator as stauth

import config
from src.pipeline import run_pipeline
from src.product_master import load_product_master, save_product_master
from src.shopee_api import ShopeeAPIError, ShopeeClient, ShopeeCredentials
from src.shopee_listing import build_sg_unlisted_payload


def _secret(name: str, default: str = "") -> str:
    """Read a Streamlit secret first, then an environment variable."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = os.getenv(name, default)
    return str(value).strip() if value is not None else default


def _render_shopee_connection() -> None:
    st.subheader("🔌 Shopee API接続")
    required = ("SHOPEE_PARTNER_ID", "SHOPEE_PARTNER_KEY", "SHOPEE_REDIRECT_URL")
    missing = [name for name in required if not _secret(name)]
    if missing:
        st.warning("API接続設定が未完了です（秘密情報は画面には表示しません）。")
        st.caption("未設定: " + ", ".join(missing))
        return

    try:
        client = ShopeeClient(ShopeeCredentials(
            partner_id=int(_secret("SHOPEE_PARTNER_ID")),
            partner_key=_secret("SHOPEE_PARTNER_KEY"),
            redirect_url=_secret("SHOPEE_REDIRECT_URL"),
            base_url=_secret("SHOPEE_BASE_URL", "https://partner.shopeemobile.com"),
        ))
    except ValueError:
        st.error("SHOPEE_PARTNER_ID の形式が正しくありません。")
        return

    st.link_button("SG/MY店舗をShopeeで認証", client.authorization_url())

    auth_code = st.query_params.get("code")
    auth_shop_id = st.query_params.get("shop_id")
    if auth_code and auth_shop_id:
        st.success(f"Shopeeから認証結果を受信しました（Shop ID: {auth_shop_id}）")
        if st.button("認証コードをAccess Tokenへ交換", type="primary"):
            try:
                token_data = client.exchange_authorization_code(auth_code, int(auth_shop_id))
                st.session_state["new_shopee_shop_id"] = str(auth_shop_id)
                st.session_state["new_shopee_access_token"] = token_data["access_token"]
                st.session_state["new_shopee_refresh_token"] = token_data.get("refresh_token", "")
                st.query_params.clear()
                st.rerun()
            except (KeyError, ValueError, requests.RequestException, ShopeeAPIError) as exc:
                st.error(f"トークン取得失敗: {exc}")

    if st.session_state.get("new_shopee_access_token"):
        st.success("Access Tokenを取得しました。秘密設定へ保存するまで画面を閉じないでください。")
        st.text_input("認証済みShop ID", value=st.session_state["new_shopee_shop_id"], disabled=True)
        st.text_input("新しいAccess Token", value=st.session_state["new_shopee_access_token"], type="password", disabled=True)
        st.text_input("新しいRefresh Token", value=st.session_state.get("new_shopee_refresh_token", ""), type="password", disabled=True)
    cols = st.columns(2)
    for col, market in zip(cols, ("SG", "MY")):
        shop_id_text = _secret(f"SHOPEE_{market}_SHOP_ID")
        access_token = _secret(f"SHOPEE_{market}_ACCESS_TOKEN")
        with col:
            st.markdown(f"**{market}店舗**")
            if not shop_id_text or not access_token:
                st.info("未接続（Shop IDまたはAccess Tokenが未設定）")
                continue
            if st.button(f"{market} 接続テスト", key=f"test_{market.lower()}_connection"):
                try:
                    info = client.get_shop_info(access_token, int(shop_id_text))
                    shop_name = info.get("shop_name") or info.get("shop_id") or shop_id_text
                    st.success(f"接続成功: {shop_name}")
                except (ValueError, requests.RequestException, ShopeeAPIError) as exc:
                    st.error(f"接続失敗: {exc}")


# ----------------------------------------------------------------------
# CLI (dry-run)
# ----------------------------------------------------------------------
def run_dry_run() -> None:
    result = run_pipeline(dry_run=True, refresh_inventory=True)

    print("\n=== dry-run 結果 ===")
    print(f"検査商品数: {result.total_rows}")
    print(f"READY_TO_LIST件数: {result.ready_count}")
    print("ステータス内訳:")
    for status, count in sorted(result.status_counts.items()):
        print(f"  {status}: {count}")

    if result.settings_missing:
        print(f"\n[警告] .envの未設定項目: {', '.join(result.settings_missing)}")
        print("      .env.example を参考に .env を作成/編集してください。")

    if result.sg_excel_written is not None:
        print(f"\nSG Excel生成: {result.sg_excel_written}件 -> {config.SG_OUTPUT_PATH}")
    else:
        print(f"\nSG Excel生成: スキップ({result.sg_excel_error})")

    if result.my_excel_written is not None:
        print(f"MY Excel生成: {result.my_excel_written}件 -> {config.MY_OUTPUT_PATH}")
    else:
        print(f"MY Excel生成: スキップ({result.my_excel_error})")

    print(f"\nログ: {config.LOGS_DIR / 'app.log'}")


# ----------------------------------------------------------------------
# Streamlit 管理画面
# ----------------------------------------------------------------------
def run_streamlit_app() -> None:
    st.set_page_config(page_title="Shopee ドラッグストア無在庫販売 管理画面", layout="wide")

    # 30-day signed login cookie. Credentials and signing key stay in Secrets.
    review_user = _secret("REVIEW_USERNAME")
    review_password = _secret("REVIEW_PASSWORD")
    cookie_key = _secret("AUTH_COOKIE_KEY")
    if not review_user or not review_password or not cookie_key:
        st.error("Login is not configured. Set REVIEW_USERNAME, REVIEW_PASSWORD and AUTH_COOKIE_KEY.")
        st.stop()

    credentials = {
        "usernames": {
            review_user: {
                "email": "",
                "first_name": "Ken",
                "last_name": "Asano",
                "password": review_password,
            }
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        "ken_shopee_login",
        cookie_key,
        30,
    )
    authenticator.login()
    if st.session_state.get("authentication_status") is False:
        st.error("Invalid username or password")
        st.stop()
    if st.session_state.get("authentication_status") is not True:
        st.stop()

    st.title("🧴 Shopee ドラッグストア無在庫販売 管理画面 (V2)")

    authenticator.logout("Sign out", "main")

    _render_shopee_connection()
    st.divider()

    if not config.PRODUCT_MASTER_PATH.exists():
        st.error(f"商品マスターが見つかりません: {config.PRODUCT_MASTER_PATH}")
        return

    df = load_product_master(config.PRODUCT_MASTER_PATH)

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    if col_a.button("① 商品検査(全項目)"):
        with st.spinner("検査中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=True)
        st.success(f"完了: READY_TO_LIST {result.ready_count}件 / 全{result.total_rows}件")
        if result.settings_missing:
            st.warning(f".env未設定項目: {', '.join(result.settings_missing)}")
        st.rerun()

    if col_b.button("② 画像確認のみ"):
        with st.spinner("画像確認中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        st.success("画像確認を含む全検査を実行しました")
        st.rerun()

    if col_c.button("③ 利益再計算"):
        with st.spinner("利益再計算中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        st.success("利益を再計算しました")
        st.rerun()

    if col_d.button("④ SG Excel生成"):
        with st.spinner("SG Excel生成中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        if result.sg_excel_written is not None:
            st.success(f"SG Excel生成完了: {result.sg_excel_written}件")
        else:
            st.error(result.sg_excel_error)

    if col_e.button("⑤ MY Excel生成"):
        with st.spinner("MY Excel生成中..."):
            result = run_pipeline(dry_run=True, refresh_inventory=False)
        if result.my_excel_written is not None:
            st.success(f"MY Excel生成完了: {result.my_excel_written}件")
        else:
            st.error(result.my_excel_error)

    st.divider()
    st.subheader("商品一覧")

    display_cols = [
        "item_id", "image_main_url", "product_name_jp", "product_name_en",
        "brand", "purchase_price_jpy", "sg_price", "my_price",
        "profit_sg_jpy", "profit_my_jpy", "source_store",
        "source_stock_status", "image_license_status", "image_match_status",
        "listing_status",
    ]
    display_cols = [c for c in display_cols if c in df.columns]

    st.dataframe(
        df[display_cols],
        column_config={
            "image_main_url": st.column_config.ImageColumn("画像", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("🇸🇬 SG 1件目の自動出品テスト")
    st.caption(
        "安全のため、最初は公開せずUNLIST（非公開）で作成します。"
        "医薬品・サプリ、架空データ、未確認画像は自動的に止めます。"
    )
    ready_rows = df[df["listing_status"] == config.ListingStatus.READY_TO_LIST]
    preview_options = ready_rows["item_id"].astype(str).tolist()
    preview_item_id = st.selectbox(
        "テスト対象item_id", options=[""] + preview_options, key="sg_preview_item_id"
    )
    if preview_item_id:
        preview_row = ready_rows.loc[
            ready_rows["item_id"].astype(str) == preview_item_id
        ].iloc[0].to_dict()
        preflight = build_sg_unlisted_payload(preview_row)
        st.write(f"商品名: {preview_row.get('product_name_en', '')}")
        st.write(f"SG価格: {preview_row.get('sg_price', '')} SGD")
        if preflight.ready:
            st.success("非公開テスト登録の準備が整っています。")
            st.info("実登録ボタンは、商品・カテゴリ・物流・画像IDの最終確認後に有効化します。")
        else:
            st.warning("この商品はまだShopeeへ送りません。次の確認が必要です。")
            for blocker in preflight.blockers:
                st.write(f"・{blocker}")
    elif preview_options:
        st.info("上の欄から1件選ぶと、出品前の安全検査結果を表示します。")
    else:
        st.warning("READY_TO_LISTの商品がありません。先に①商品検査を実行してください。")

    st.divider()
    st.subheader("停止候補にする")
    st.caption(
        "注意: このボタンはShopee上の出品を実際には停止しません。"
        "listing_status を STOP_CANDIDATE に変更するだけです。"
        "実際の出品停止はShopeeセラーセンター(またはSellBridge)で行ってください。"
    )
    item_ids = df["item_id"].tolist()
    target = st.selectbox("対象item_id", options=[""] + item_ids)
    if st.button("停止候補にする", disabled=(target == "")):
        idx = df.index[df["item_id"] == target][0]
        df.at[idx, "listing_status"] = config.ListingStatus.STOP_CANDIDATE
        save_product_master(df, config.PRODUCT_MASTER_PATH)
        st.success(f"item_id={target} を停止候補(STOP_CANDIDATE)にしました")
        st.rerun()


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        run_dry_run()
    else:
        run_streamlit_app()
