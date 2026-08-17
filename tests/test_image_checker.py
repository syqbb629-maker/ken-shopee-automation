from src.image_checker import check_image_file, evaluate_image


def test_local_image_exists_and_valid():
    ok, reason = check_image_file("tests/fixtures/sample.jpg", "")
    assert ok is True


def test_local_image_missing():
    ok, reason = check_image_file("tests/fixtures/does_not_exist.jpg", "")
    assert ok is False


def test_no_image_specified():
    ok, reason = check_image_file("", "")
    assert ok is False


def test_evaluate_image_passes_when_all_conditions_met():
    row = {
        "image_main_local": "tests/fixtures/sample.jpg",
        "image_main_url": "",
        "image_license_status": "APPROVED",
        "image_match_status": "MATCHED",
    }
    result = evaluate_image(row)
    assert result.passes is True


def test_evaluate_image_fails_without_license_approval():
    row = {
        "image_main_local": "tests/fixtures/sample.jpg",
        "image_main_url": "",
        "image_license_status": "REVIEW_REQUIRED",
        "image_match_status": "MATCHED",
    }
    result = evaluate_image(row)
    assert result.passes is False


def test_evaluate_image_fails_without_match():
    row = {
        "image_main_local": "tests/fixtures/sample.jpg",
        "image_main_url": "",
        "image_license_status": "APPROVED",
        "image_match_status": "MISMATCH",
    }
    result = evaluate_image(row)
    assert result.passes is False


def test_evaluate_image_fails_when_file_missing():
    row = {
        "image_main_local": "tests/fixtures/does_not_exist.jpg",
        "image_main_url": "",
        "image_license_status": "APPROVED",
        "image_match_status": "MATCHED",
    }
    result = evaluate_image(row)
    assert result.passes is False
