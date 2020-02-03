import abc
import math
import datetime
import pandas as pd
import numpy as np
import typing
import operator
import re
from dataclasses import dataclass

from . import column
from .errors import PanSchArgumentError, PanSchNoIndexError
from pandas_schema.validation_warning import ValidationWarning
from pandas_schema.index import PandasIndexer
from pandas.api.types import is_categorical_dtype, is_numeric_dtype


class BaseValidation(abc.ABC):
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

    def message(self, warning: ValidationWarning) -> str:
        pass


class SeriesValidation(BaseValidation):
    """
    A _SeriesValidation validates a DataFrame by selecting a single series from it, and
    applying some validation to it
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


class IndexSeriesValidation(SeriesValidation):
    """
    Selects a series from the DataFrame, using label or position-based indexes that can be provided at instantiation
    or later
    """

    def __init__(self, index: PandasIndexer = None, message: str = None):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
        Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        self.index = index
        self.custom_message = message

    def message(self, warning: ValidationWarning):
        """
        Gets a message describing how the DataFrame cell failed the validation
        This shouldn't really be overridden, instead override default_message so that users can still set per-object
        messages
        :return:
        """
        if self.index.type == 'position':
            prefix = self.index.index
        else:
            prefix = '"{}"'.format(self.index.index)

        if self.custom_message:
            suffix = self.custom_message
        else:
            suffix = self.default_message(warning)

        return "Column {} {}".format(prefix, suffix)

    @property
    def readable_name(self, **kwargs):
        """
        A readable name for this validation, to be shown in validation warnings
        """
        return type(self).__name__

    def default_message(self, warning: ValidationWarning) -> str:
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

        return self.index(df)

    @abc.abstractmethod
    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        pass


class BooleanSeriesValidation(IndexSeriesValidation):
    """
    Validation is defined by the function :py:meth:~select_cells that returns a boolean series.
        Each cell that has False has failed the validation.

        Child classes need not create their own :py:class:~pandas_schema.core.BooleanSeriesValidation.Warning subclass,
        because the data is in the same form for each cell. You need only define a :py:meth~default_message.
    """

    @abc.abstractmethod
    def select_cells(self, series: pd.Series) -> pd.Series:
        """
        A BooleanSeriesValidation must return a boolean series. Each cell that has False has failed the
            validation
        :param series: The series to validate
        """
        pass

    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        failed = ~self.select_cells(series)
        cells = series[failed]
        return (
            ValidationWarning(self, {
                'row': row_idx,
                'value': cell
            }) for row_idx, cell in cells.items()
        )
