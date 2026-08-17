from config import Settings, ListingStatus
from src.product_validator import validate_product
from src.profit_calculator import ShippingRate

RATES = [
    ShippingRate("SG", 0, 250, 1800, "Standard"),
    ShippingRate("MY", 0, 250, 1700, "Standard"),
]

GOOD_SETTINGS = Settings(
    exchange_rate_sgd=112.0,
    exchange_rate_myr=34.0,
    shopee_fee_rate_sg=0.06,
    shopee_fee_rate_my=0.06,
    payment_fee_rate=0.02,
    other_costs_jpy=50,
    missing_fields=[],
)


def base_row(**overrides) -> dict:
    row = {
        "item_id": "T001",
        "jan_code": "1234567890123",
        "brand": "TestBrand",
        "product_name_jp": "テスト商品",
        "product_name_en": "Test Product 40g",
        "category": "Skincare",
        "volume": "40g",
        "country_of_origin": "Japan",
        "purchase_price_jpy": "780",
        "source_store": "TestStore",
        "source_url": "https://example.com/item/1",
        "source_checked_at": "",
        "source_stock_status": "IN_STOCK",
        "image_main_local": "tests/fixtures/sample.jpg",
        "image_main_url": "",
        "image_2_url": "",
        "image_3_url": "",
        "image_source_url": "",
        "image_license_status": "APPROVED",
        "image_match_status": "MATCHED",
        "net_weight_g": "40",
        "shipping_weight_g": "120",
        "package_length_cm": "4",
        "package_width_cm": "4",
        "package_height_cm": "12",
        "weight_source": "manufacturer",
        "sg_price": "32.9",
        "my_price": "99.9",
        "stock": "2",
        "sku_sg": "TB-SG-001",
        "sku_my": "TB-MY-001",
        "description_en": "Brand: TestBrand\nShips from Japan",
        "regulation_status": "",
        "shipping_status": "",
        "profit_sg_jpy": "",
        "profit_my_jpy": "",
        "listing_status": "",
    }
    row.update(overrides)
    return row


def test_no_image_is_not_ready():
    row = base_row(image_main_local="", image_main_url="")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.IMAGE_REVIEW_REQUIRED


def test_image_license_not_approved_is_not_ready():
    row = base_row(image_license_status="REVIEW_REQUIRED")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.IMAGE_REVIEW_REQUIRED


def test_image_mismatch_is_not_ready():
    row = base_row(image_match_status="MISMATCH")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.IMAGE_REVIEW_REQUIRED


def test_missing_weight_is_not_ready():
    row = base_row(shipping_weight_g="")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.WEIGHT_REVIEW_REQUIRED


def test_estimated_weight_source_is_not_ready():
    row = base_row(weight_source="estimated")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.WEIGHT_REVIEW_REQUIRED


def test_no_shipping_rate_match_is_not_ready():
    row = base_row(shipping_weight_g="99999")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.SHIPPING_RATE_MISSING


def test_missing_purchase_price_is_not_ready():
    row = base_row(purchase_price_jpy="")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.DATA_INCOMPLETE


def test_unknown_stock_is_not_ready():
    row = base_row(source_stock_status="UNKNOWN")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.OUT_OF_STOCK


def test_low_profit_product():
    row = base_row(sg_price="1.0", my_price="1.0")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.LOW_PROFIT


def test_regulated_product_is_flagged():
    row = base_row(product_name_jp="テスト 第2類医薬品 かぜ薬")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.REGULATION_REVIEW_REQUIRED


def test_normal_product_is_ready():
    row = base_row()
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.READY_TO_LIST


def test_japanese_in_english_title_is_not_ready():
    row = base_row(product_name_en="Curel キュレル Moisture Cream 40g")
    result = validate_product(row, shipping_rates=RATES, settings=GOOD_SETTINGS)
    assert result.listing_status == ListingStatus.DATA_INCOMPLETE
