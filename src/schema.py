"""
schema.py
----------
data/product_master.xlsx の列定義(V2仕様11)。
全モジュールがこの列名を共通で参照する。
"""

PRODUCT_MASTER_COLUMNS = [
    "item_id",
    "jan_code",
    "brand",
    "product_name_jp",
    "product_name_en",
    "category",
    "volume",
    "country_of_origin",

    "purchase_price_jpy",
    "source_store",
    "source_url",
    "source_checked_at",
    "source_stock_status",

    "image_main_local",
    "image_main_url",
    "image_2_url",
    "image_3_url",
    "image_source_url",
    "image_license_status",
    "image_match_status",

    "net_weight_g",
    "shipping_weight_g",
    "package_length_cm",
    "package_width_cm",
    "package_height_cm",
    "weight_source",

    "sg_price",
    "my_price",
    "stock",

    "sku_sg",
    "sku_my",

    "description_en",

    "regulation_status",
    "shipping_status",

    "profit_sg_jpy",
    "profit_my_jpy",

    "listing_status",
]

# 医薬品・サプリ等、除外対象を検出するためのキーワード(V2仕様15)
REGULATED_KEYWORDS_EN = [
    "medicine", "drug", "otc medicine", "supplement", "vitamin supplement",
    "herbal supplement", "painkiller", "cold medicine", "eye drops", "laxative",
]
REGULATED_KEYWORDS_JP = [
    "医薬品", "第1類", "第2類", "第3類", "指定医薬部外品", "サプリ", "健康食品",
]

# エアゾール・危険物検出キーワード(V2仕様16)
HAZARDOUS_KEYWORDS_EN = [
    "aerosol", "spray can", "flammable", "gas",
    "high concentration alcohol", "strong bleach",
]

# 商品説明で断定してはいけない効能表現(V2仕様14)
FORBIDDEN_CLAIM_KEYWORDS = [
    "cures", "heals", "treats", "medical effect",
    "guaranteed whitening", "anti-aging guarantee",
]
