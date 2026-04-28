import pandas as pd

from src.features import build_feature_frame, split_train_validation


def test_feature_builder_creates_expected_columns():
    train = pd.DataFrame(
        [
            {
                "Store": 1,
                "DayOfWeek": 5,
                "Date": "2015-07-31",
                "Sales": 5263,
                "Customers": 555,
                "Open": 1,
                "Promo": 1,
                "StateHoliday": "0",
                "SchoolHoliday": 1,
            }
        ]
    )
    store = pd.DataFrame(
        [
            {
                "Store": 1,
                "StoreType": "c",
                "Assortment": "a",
                "CompetitionDistance": 1270.0,
                "CompetitionOpenSinceMonth": 9,
                "CompetitionOpenSinceYear": 2008,
                "Promo2": 0,
                "Promo2SinceWeek": 0,
                "Promo2SinceYear": 0,
                "PromoInterval": None,
            }
        ]
    )

    frame = build_feature_frame(train, store)
    assert "CompetitionOpenMonths" in frame.columns
    assert "Promo2Active" in frame.columns
    assert frame.loc[0, "Month"] == 7


def test_temporal_split_places_recent_rows_in_validation():
    frame = pd.DataFrame(
        {
            "Date": pd.date_range("2015-01-01", periods=100, freq="D"),
            "Sales": range(100),
        }
    )
    train_frame, validation_frame = split_train_validation(frame, validation_days=10)
    assert len(train_frame) > len(validation_frame)
    assert validation_frame["Date"].min() > train_frame["Date"].max()

