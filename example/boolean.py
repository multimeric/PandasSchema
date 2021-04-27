from pandas_schema import Column, Schema
from pandas_schema.validation import MatchesPatternValidation, CanConvertValidation, CustomSeriesValidation
import pandas as pd

schema = Schema([
    Column('col1', [
        CanConvertValidation(int) |
        (
            CustomSeriesValidation(lambda x: x.str.len() > 1, 'Doesn\'t have more than 1 character') &
            MatchesPatternValidation('a')
        )
    ])
])

test_data = pd.DataFrame({
    'col1': [
        'an',
        '13',
        'a',
        '8',
        'the'
    ]
})

errors = schema.validate(test_data)

for error in errors:
    print('"{}" failed!'.format(error.value))
