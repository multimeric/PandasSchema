import abc
import math
import datetime
import pandas as pd
import numpy as np
import typing
import operator

from . import column
from .validation_warning import ValidationWarning
from .errors import PanSchArgumentError, PanSchNoIndexError
from pandas.api.types import is_categorical_dtype, is_numeric_dtype


class _BaseValidation(abc.ABC):
    @abc.abstractmethod
    def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
        """
        Validates a data frame
        :param df: Data frame to validate
        :return: All validation failures detected by this validation
        """


class _SeriesValidation(_BaseValidation):
    """
    A _SeriesValidation validates a DataFrame by selecting a single series from it, and applying some validation
    to it
    """

    @abc.abstractmethod
    def select_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Selects a series from the DataFrame that will be validated
        """

    @abc.abstractmethod
    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        """
        Validate a single series
        """

    def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
        series = self.select_series(df)
        return self.validate_series(series)


class IndexSeriesValidation(_SeriesValidation):
    """
    Selects a series from the DataFrame, using label or position-based indexes that can be provided at instantiation
    or later
    """

    def __init__(self, index: typing.Union[int, str] = None, position: bool = False):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
        :param position: If true, the index is a position along the axis (ie, index=0 indicates the first element).
        Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        self.index = column
        self.position = position

    def select_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Select a series using the data stored in this validation
        """
        if self.index is None:
            raise PanSchNoIndexError()

        if self.position:
            return df.iloc[self.index]
        else:
            return df.loc[self.index]
