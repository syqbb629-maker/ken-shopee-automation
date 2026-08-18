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
