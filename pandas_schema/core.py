import abc
import math
import datetime
import pandas as pd
import numpy as np
import typing
import operator
import re

from . import column
from .validation_warning import ValidationWarning
from .errors import PanSchArgumentError, PanSchNoIndexError
from pandas.api.types import is_categorical_dtype, is_numeric_dtype


class _BaseValidation(abc.ABC):
    """
    A validation is, broadly, just a function that maps a data frame to a list of errors
    """
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

    def __init__(self, index: typing.Union[int, str] = None, position: bool = False, message:str=None):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
        :param position: If true, the index is a position along the axis (ie, index=0 indicates the first element).
        Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        self.index = index
        self.position = position
        self.custom_message = message

    @property
    def message(self):
        """
        Gets a message describing how the DataFrame cell failed the validation
        This shouldn't really be overridden, instead override default_message so that users can still set per-object
        messages
        :return:
        """
        return self.custom_message or self.default_message

    @property
    def readable_name(self):
        """
        A readable name for this validation, to be shown in validation warnings
        """
        return type(self).__name__

    @property
    def default_message(self) -> str:
        """
        Create a message to be displayed whenever this validation fails
        This should be a generic message for the validation type, but can be overwritten if the user provides a
        message kwarg
        """
        return 'failed the {}'.format(self.readable_name)

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

    @abc.abstractmethod
    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        pass
