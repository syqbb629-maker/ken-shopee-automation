from src.shopee_listing import build_sg_unlisted_payload


def valid_row(**updates):
    row = {
        "listing_status": "READY_TO_LIST",
        "product_name_jp": "洗顔フォーム 100g",
        "product_name_en": "Japanese Facial Cleanser 100g",
        "description_en": "New facial cleanser. Ships from Japan.",
        "brand": "Real Brand",
        "source_url": "https://supplier.invalid/products/123",
        "sg_price": 19.9,
        "shipping_weight_g": 180,
        "stock": 2,
        "package_height_cm": 16,
        "package_length_cm": 5,
        "package_width_cm": 5,
        "shopee_sg_category_id": 12345,
        "shopee_sg_logistic_id": 80001,
        "shopee_image_id": "sg-image-id",
        "sku_sg": "SG-001",
    }
    row.update(updates)
    return row


def test_builds_unlisted_payload_only():
    result = build_sg_unlisted_payload(valid_row())
    assert result.ready
    assert result.payload["item_status"] == "UNLIST"
    assert result.payload["weight"] == 0.18
    assert result.payload["seller_stock"] == [{"stock": 2}]


def test_blocks_placeholder_and_missing_shopee_ids():
    result = build_sg_unlisted_payload(valid_row(
        brand="SunCare Japan",
        source_url="https://example-drugstore.example.com/item/ITEM001",
        shopee_sg_category_id="",
        shopee_image_id="",
    ))
    assert not result.ready
    assert any("テスト用ブランド" in reason for reason in result.blockers)
    assert any("仕入先URL" in reason for reason in result.blockers)
    assert any("カテゴリID" in reason for reason in result.blockers)
    assert any("画像ID" in reason for reason in result.blockers)


def test_blocks_medicine_and_supplements():
    result = build_sg_unlisted_payload(valid_row(product_name_en="Vitamin Supplement 30 Tablets"))
    assert not result.ready
    assert any("除外対象" in reason for reason in result.blockers)
