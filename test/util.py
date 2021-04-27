import pandas as pd
from pandas_schema.core import BaseValidation
from pandas_schema.validation_warning import ValidationWarning
import typing


def get_warnings(validator: BaseValidation, series: typing.Union[list, pd.Series]) -> typing.Collection[
    ValidationWarning]:
    """
    Tests a validator by asserting that it generates the amount of warnings
    :param series_dtype: Explicitly specifies the dtype for the generated Series
    :param series: The series to check
    :param expected_result: Whether the elements in this series should pass the validation
    :param msg: The message to display if this test fails
    """

    # # Check that self.validator is correct
    # if not self.validator or not isinstance(self.validator, BooleanSeriesValidation, index=0):
    #     raise ValueError('The class must have the validator field set to an instance of a Validation subclass')
    #
    # # Ensure we're comparing series correctly
    # self.addTypeEqualityFunc(pd.Series, self.seriesEquality)

    df = pd.Series(series).to_frame()
    warnings = validator.validate(df)
    return list(warnings)
    #
    # # Now find any items where their validation does not correspond to the expected_result
    # for item, result in zip(series, results):
    #     with self.subTest(value=item):
    #         self.assertEqual(result, expected_result, msg)

