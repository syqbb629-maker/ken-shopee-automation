【重要】このフォルダには本物のShopee公式テンプレートを置いてください

本プロジェクトには、Shopee公式のMass Uploadテンプレートファイルが
含まれていません(偽物のテンプレートを「公式」として代用することは
仕様上禁止されているため、意図的に同梱していません)。

以下の2ファイルを、Shopeeセラーセンターからダウンロードして
このフォルダに配置してください。

  templates/shopee_sg_template.xlsx   ← Shopee Singapore公式Mass Uploadテンプレート
  templates/shopee_my_template.xlsx   ← Shopee Malaysia公式Mass Uploadテンプレート

入手方法(目安):
  Shopeeセラーセンター(Seller Centre) にログイン
  → 商品管理(Product) → 一括アップロード(Mass Upload / Bulk Upload)
  → テンプレートをダウンロード

配置後、以下を実行すると自動的に読み込まれます:

  python app.py --dry-run
  または Streamlit管理画面の「SG Excel生成」「MY Excel生成」ボタン

このファイルが配置されていない状態でExcel生成を実行すると、
「Shopee公式テンプレートが見つかりません」というエラーメッセージが
表示されます(これは正常な動作です)。
