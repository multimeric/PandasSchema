import pandas as pd
import pytest

from pandas_schema import ValidationWarning
from pandas_schema.df_validations import DistinctRowValidation
from pandas.testing import assert_series_equal


@pytest.mark.parametrize(['df', 'result', 'kwargs'], [
    [
        # By default, all duplicates should be marked
        pd.DataFrame([
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
        ]),
        [
            False, False, False, False
        ],
        dict()
    ],
    [
        # With keep='first', the first duplicates are okay
        pd.DataFrame([
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
        ]),
        [
            True, True, False, False
        ],
        dict(keep='first')
    ],
    [
        # With keep='last', the last duplicates are okay
        pd.DataFrame([
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
            ['a', 'a', 'a'],
            ['a', 'b', 'c'],
        ]),
        [
            False, False, True, True
        ],
        dict(keep='last')
    ]
])
def test_distinct_row_validation(df, result, kwargs):
    validator = DistinctRowValidation(**kwargs)

    # Test the internal validation that produces a Series
    series = validator.validate_df(df)
    assert_series_equal(series, pd.Series(result))

    # Test the public method that returns warnings
    # The number of warnings should be equal to the number of failures
    warnings = validator.validate(df)
    assert len(warnings) == result.count(False)
    assert isinstance(warnings[0], ValidationWarning)

