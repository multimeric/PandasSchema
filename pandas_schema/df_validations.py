from abc import abstractmethod
from typing import Union

import pandas as pd

from . import ValidationWarning
from .core import BaseValidation, ValidationScope
from .index import DualAxisIndexer, BooleanIndexer


class DfRowValidation(BaseValidation):
    """
    Validates the entire DF at once, by returning a boolean Series corresponding to row indices that pass or fail
    """
    def get_failed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        passed = self.get_passed_index(df)
        return passed.invert(axis=0)

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        series = self.validate_df(df)
        return DualAxisIndexer(
            row_index=BooleanIndexer(series, axis=0),
            col_index=BooleanIndexer(True, axis=1)
        )

    @abstractmethod
    def validate_df(self, df: pd.DataFrame) -> pd.Series:
        """
        Validate the DF by returning a boolean series
        Args:
            df: The DF to validate

        Returns: A boolean Series whose indices correspond to the row indices of the DF. If the Series has the value
        True, this means the corresponding row passed the validation

        Example:
            If we were for some reason validating that each row contains values higher than any element in the previous
            row::

                1 2 3
                4 5 6
                1 1 1

            The correct boolean Series to return here would be::

                True
                True
                False
        """


class DistinctRowValidation(DfRowValidation, scope=ValidationScope.ROW):
    def __init__(self, keep: Union[bool, str] = False, **kwargs):
        """
        Args:
            keep: Refer to the pandas docs:
                "first" indicates that duplicates fail the validation except for the first occurrence.
                "last" indicates that duplicates fail the validation except for the last occurrence.
                False indicates that all duplicates fail the validation
        """
        super().__init__(**kwargs)
        self.keep = keep

    def prefix(self, warning: ValidationWarning):
        return '{{Row {row}}}'.format(**warning.props)

    def validate_df(self, df: pd.DataFrame) -> pd.Series:
        # We invert here because pandas gives duplicates a True value but we want them to be False as in "invalid"
        return ~df.duplicated(keep=self.keep)
