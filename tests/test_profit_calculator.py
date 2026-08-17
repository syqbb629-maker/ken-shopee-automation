from config import Settings
from src.profit_calculator import ShippingRate, calculate_profit, find_shipping_cost

RATES = [
    ShippingRate("SG", 0, 250, 1800, "Standard"),
    ShippingRate("SG", 251, 500, 2300, "Standard"),
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


def test_find_shipping_cost_hit():
    rate = find_shipping_cost(RATES, "SG", 120)
    assert rate is not None
    assert rate.shipping_cost_jpy == 1800


def test_find_shipping_cost_miss():
    rate = find_shipping_cost(RATES, "SG", 9999)
    assert rate is None


def test_shipping_rate_missing_status():
    result = calculate_profit(
        market="SG",
        sell_price_local=15.9,
        purchase_price_jpy=780,
        shipping_weight_g=9999,
        rates=RATES,
        settings=GOOD_SETTINGS,
    )
    assert result.status == "SHIPPING_RATE_MISSING"


def test_data_incomplete_missing_purchase_price():
    result = calculate_profit(
        market="SG",
        sell_price_local=15.9,
        purchase_price_jpy=None,
        shipping_weight_g=120,
        rates=RATES,
        settings=GOOD_SETTINGS,
    )
    assert result.status == "DATA_INCOMPLETE"


def test_config_missing_when_settings_incomplete():
    incomplete = Settings(missing_fields=["EXCHANGE_RATE_SGD"])
    result = calculate_profit(
        market="SG",
        sell_price_local=15.9,
        purchase_price_jpy=780,
        shipping_weight_g=120,
        rates=RATES,
        settings=incomplete,
    )
    assert result.status == "CONFIG_MISSING"


def test_profit_calculated_correctly():
    result = calculate_profit(
        market="SG",
        sell_price_local=15.9,
        purchase_price_jpy=780,
        shipping_weight_g=120,
        rates=RATES,
        settings=GOOD_SETTINGS,
    )
    assert result.status == "OK"
    # 手計算: 15.9*112=1780.8, fee=106.848, payment=35.616
    # profit = 1780.8 - 780 - 1800 - 106.848 - 35.616 - 50 = -991.664 (赤字ケース)
    assert result.profit_jpy is not None
    assert round(result.profit_jpy, 1) == round(
        15.9 * 112.0 - 780 - 1800 - (15.9 * 112.0 * 0.06) - (15.9 * 112.0 * 0.02) - 50, 1
    )


def test_low_profit_case_is_negative():
    # 送料が販売額を上回るケース(赤字テスト用)
    result = calculate_profit(
        market="SG",
        sell_price_local=15.9,
        purchase_price_jpy=780,
        shipping_weight_g=120,
        rates=RATES,
        settings=GOOD_SETTINGS,
    )
    assert result.profit_jpy is not None and result.profit_jpy <= 0
