# Shopee ドラッグストア無在庫販売システム V2

日本の大型ドラッグストアで買える日用品(医薬品・サプリ等は除外)を、
Shopee Singapore / Malaysia向けに無在庫販売するための業務支援ツールです。

商品検査 → 画像確認 → 在庫確認 → 重量/送料確認 → 利益計算 →
READY_TO_LIST判定 → Shopee公式Mass Upload Excel生成、までを支援します。

**このツールは自動でShopeeに出品しません。** 最終的な出品はご自身で
Shopeeセラーセンター(またはSellBridge)からMass Uploadファイルを
アップロードして行ってください。安全のため、意図的に自動出品APIは
実装していません。

---

## 0. 最初に必ず読んでください

- 本プロジェクトには **Shopee公式のMass Uploadテンプレート** は
  含まれていません。`templates/` フォルダの案内(
  `README_PLACE_TEMPLATES_HERE.txt`)に従い、ご自身のShopeeセラーセンター
  から本物のテンプレートをダウンロードして配置してください。
  配置するまでは商品検査・利益計算は動作しますが、Excel生成の手順だけ
  スキップされます(エラーメッセージが表示されますが、正常な動作です)。
- `data/product_master.xlsx` にはサンプル(デモ用)商品が5件だけ
  入っています。実運用では、ご自身の商品データに置き換えてください。
- `data/shipping_rates.csv` の送料は仮の値です。実際の国際送料に
  合わせて編集してください。
- `.env` の為替レート・Shopee手数料率も仮の初期値です。必ず最新の
  実際の値に更新してください。

---

## 1. Windows 11 セットアップ手順

### 1) ZIPを解凍

`shopee_drugstore_dropship_v2.zip` を右クリック →
「すべて展開」でお好きな場所(例: デスクトップ)に解凍します。

### 2) フォルダを開く

解凍してできた `shopee_drugstore_dropship_v2` フォルダを開きます。

### 3) コマンドプロンプト/PowerShellを開く

フォルダの中で、アドレスバー(パスが表示されている部分)をクリックして
`cmd` と入力し Enter を押すと、そのフォルダでコマンドプロンプトが
開きます。(PowerShellでも同様に使えます)

### 4) 仮想環境を作成

```
python -m venv venv
```

※ `python` コマンドが見つからないと言われる場合は、Python 3.10以上を
Microsoft StoreまたはPython公式サイトからインストールしてから
やり直してください。

### 5) 仮想環境を有効化

```
venv\Scripts\activate
```

行の先頭に `(venv)` と表示されればOKです。

### 6) 必要なライブラリをインストール

```
pip install -r requirements.txt
```

### 7) .envファイルを作成

```
copy .env.example .env
```

作成された `.env` をメモ帳等で開き、為替レート・Shopee手数料率などを
実際の値に更新してください(サンプル値のままでも動作はします)。

### 8) dry-run(試験実行)

Shopeeへは何も送信しません。安全にお試しいただけます。

```
python app.py --dry-run
```

商品検査・画像確認・在庫確認・利益計算・READY判定・SG/MY Excel生成
(公式テンプレート配置済みの場合)・ログ保存(`logs/app.log`)までが
実行され、結果がコンソールに表示されます。

### 9) 管理画面を開く

```
streamlit run app.py
```

自動的にブラウザが開き、商品一覧・各種ボタン(商品検査/画像確認/
利益再計算/SG Excel生成/MY Excel生成/停止候補にする)が使える画面が
表示されます。

---

## 2. 段階的な検証(安全のため)

いきなり100商品を公開しないでください。以下の順で段階的に増やして
運用を確認することを推奨します。

1. 5商品でテスト
2. 20商品に拡大
3. 100商品に拡大

`src/product_search.py` の `get_candidates(..., stage=1|2|3)` で
段階(5件/20件/100件)を切り替えられます。

---

## 3. フォルダ構成

```
shopee_drugstore_dropship_v2/
  app.py                     CLI(--dry-run) / Streamlit管理画面
  config.py                  .env読み込み・各種ステータス定数
  requirements.txt
  .env.example
  README.md

  data/
    product_master.xlsx      商品マスター(サンプル5件)
    shipping_rates.csv       送料テーブル(市場×重量帯、編集可能)
    sample_images/           デモ用サンプル画像

  templates/
    README_PLACE_TEMPLATES_HERE.txt   ← 公式テンプレート配置の案内
    (shopee_sg_template.xlsx を配置)
    (shopee_my_template.xlsx を配置)

  output/
    shopee_sg_ready.xlsx     READY_TO_LISTのみ出力(生成後)
    shopee_my_ready.xlsx     READY_TO_LISTのみ出力(生成後)

  src/
    product_search.py        商品候補取得(段階的検証対応)
    image_checker.py         画像の実在確認・利用許諾/一致確認
    product_validator.py     READY_TO_LIST判定ロジック
    profit_calculator.py     送料テーブル+.env手数料による利益計算
    title_generator.py       英語タイトル検証(日本語混入チェック)
    description_generator.py 商品説明生成(事実のみ・効能断定なし)
    shopee_excel_generator.py Shopee公式テンプレートへの書き込み
    inventory_checker.py     在庫状態の確認
    pipeline.py               上記全体を束ねる共通パイプライン
    product_master.py / schema.py  商品マスターの読み書き・列定義

  tests/
    test_profit_calculator.py
    test_product_validator.py
    test_image_checker.py
    test_shopee_excel_generator.py

  logs/
    app.log                  実行ログ
```

---

## 4. 商品マスターの主な列

`data/product_master.xlsx` の列の意味(抜粋):

| 列名 | 説明 |
|---|---|
| product_name_jp / product_name_en | 日本語名/英語名(英語は完全な英語のみ。自動翻訳では生成しません) |
| country_of_origin | 原産国。確認できた場合のみ商品説明に表示(Unknownなら非表示) |
| weight_source | manufacturer/supplier/manual/estimated。estimatedはWEIGHT_REVIEW_REQUIREDになります |
| image_license_status | APPROVED / REVIEW_REQUIRED / REJECTED |
| image_match_status | MATCHED / MISMATCH / REVIEW_REQUIRED |
| source_stock_status | IN_STOCK / LOW_STOCK / OUT_OF_STOCK / UNKNOWN |
| listing_status | READY_TO_LIST 等(下記参照) |

`listing_status` の一覧:

```
READY_TO_LIST
IMAGE_REVIEW_REQUIRED
REGULATION_REVIEW_REQUIRED
WEIGHT_REVIEW_REQUIRED
SHIPPING_REVIEW_REQUIRED
SHIPPING_RATE_MISSING
OUT_OF_STOCK
LOW_PROFIT
DISCONTINUED
DATA_INCOMPLETE
STOP_CANDIDATE
CONFIG_MISSING (.env未設定のため判定不可)
```

---

## 5. 「停止候補にする」ボタンについて

このボタンは **Shopee上の出品を実際には停止しません**。
`listing_status` を `STOP_CANDIDATE` に変更するだけです。実際の出品
停止は、Shopeeセラーセンター(またはSellBridge)で手動操作してください。

---

## 6. テストの実行方法

```
pip install -r requirements.txt
pytest tests/ -v
```

---

## 7. 安全のための優先順位

出品件数よりも安全性・正確性を優先する設計です。以下は自動で
READY_TO_LISTにしません。

- 画像が無い/実在しない/利用許諾が無い/商品と一致しない
- 重量・梱包サイズが未確認(estimated)
- 送料テーブルに該当区分が無い
- 仕入価格・在庫状態が不明
- 医薬品・サプリ等の規制対象キーワードを検出
- エアゾール・危険物のキーワードを検出
- 利益が0以下
