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

import sys
import os

import pandas as pd
import streamlit as st

import config
from src.pipeline import run_pipeline
from src.product_master import load_product_master, save_product_master


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

    # Go-Live review用の簡易ログイン。認証情報はコードに書かず、
    # Streamlit CloudのSecretsまたは環境変数で設定します。
    review_user = st.secrets.get("REVIEW_USERNAME", os.getenv("REVIEW_USERNAME", ""))
    review_password = st.secrets.get("REVIEW_PASSWORD", os.getenv("REVIEW_PASSWORD", ""))
    if not review_user or not review_password:
        st.error("Review login is not configured. Set REVIEW_USERNAME and REVIEW_PASSWORD.")
        st.stop()

    if not st.session_state.get("authenticated", False):
        st.title("Ken Shopee Automation")
        st.caption("Authorized users only")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign in", type="primary"):
            if username == review_user and password == review_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.stop()

    st.title("🧴 Shopee ドラッグストア無在庫販売 管理画面 (V2)")
    if st.button("Sign out"):
        st.session_state["authenticated"] = False
        st.rerun()

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
