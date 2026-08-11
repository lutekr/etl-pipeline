import pytest
import etl_v2 as e

test_probe = [
    {
        "zip": "85018",
        "type": "single_family",
        "year_built": 2025.0,
        "listPrice": 4498946.0,
        "lastSoldPrice": 4300076.0,
        "list_to_sold_ratio": 0.9558,
        "sqft": 5010.0,
        "price_per_sqft": 858.3,
        "stories": 1.0,
        "beds": 5.0,
        "baths": 6.0,
        "baths_full": 5.0,
        "baths_full_calc": 5.0,
        "garage": 3.0,
        "sanitized_text": "Located in the desirable Arcadia area of Phoenix, this NEW BUILD will offer unparalleled luxury & comfort across its expansive layout. The primary suite is a true retreat, featuring a vaulted wood T+G ceiling, stacked stone fireplace, and direct access to the pool and spa."
    },
    {
        "zip": "85377",
        "type": "single_family",
        "year_built": 2009.0,
        "listPrice": "1799089.0",
        "lastSoldPrice": 1750060.0,
        "list_to_sold_ratio": 0.9727,
        "sqft": 4270.0,
        "price_per_sqft": 409.85,
        "stories": 1.0,
        "beds": 5.0,
        "baths": 5.0,
        "baths_full": 4.0,
        "baths_full_calc": 4.0,
        "garage": 3.0,
        "sanitized_text": "The home is hard-wired for streaming, with Ethernet connections to all current TVs, ensuring seamless modern connectivity. Three bedroom suites are located in the main home, each offering comfort and privacy."
    },
    {
        "zip": "85037",
        "type": "single_family",
        "year_built": 1973.0,
        "listPrice": 335083.0,
        "lastSoldPrice": 328911.0,
        "list_to_sold_ratio": 0.9816,
        "sqft": 1360.0,
        "price_per_sqft": 241.85,
        "stories": 1.0,
        "beds": 4.0,
        "baths": 2.0,
        "baths_full": 1.0,
        "baths_full_calc": 1.0,
        "garage": 2.0,
        "sanitized_text": "Sharp 4 bedroom 1.75 bathroom two car garage large lot all tile floors and bath rooms new Double pane windows for lower energy bills for lower bills."
    },
    {
        "zip": "85037",
        "type": "single_family",
        "year_built": 1973.0,
        "listPrice": 429828.0,
        "lastSoldPrice": 434291.0,
        "list_to_sold_ratio": 1.0104,
        "sqft": 1510.0,
        "price_per_sqft": 287.61,
        "stories": 1.0,
        "beds": 4.0,
        "baths": 2.0,
        "baths_full": 2.0,
        "baths_full_calc": 2.0,
        "garage": 2.0,
        "sanitized_text": "The remodeled kitchen features warm wood cabinetry, quartz countertops, and brand-new stainless steel appliances to be installed this weekend. Designer bathrooms include a sleek walk-in shower with custom tile, matte black fixtures, and a modern tub surround with statement niche."
    }
]

broken_probe = [{
        "zip": "ABCDE",
        "type": "",
        "year_built": "NOT_A_YEAR",
        "listPrice": "price",
        "lastSoldPrice": "",
        "list_to_sold_ratio": "None",
        "sqft": "-",
        "price_per_sqft": "",
        "stories": "pietra",
        "beds": "duzo",
        "baths": "kilka",
        "baths_full": "",
        "baths_full_calc": "",
        "garage": "auto",
        "sanitized_text": "broken row#$% !!! @#$%"
    }]

def test_cleaner_preserves_valid_rows():
    result =  list(e.data_cleaner(test_probe))
    assert len(result) == 4
    assert result[0]["zip"] == 85018
    assert result[1]["listPrice"] == 1799089.0
    assert result[2]["beds"] == 4
    assert isinstance(result[2]["beds"], int)

def test_filter_broken_row():
    result = list(e.data_cleaner(broken_probe))
    assert len(result) == 0

def test_open_file_exception(tmp_path):
    path = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        list(e.iter_raw_file(path))
