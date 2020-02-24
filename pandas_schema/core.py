import abc
import math
import datetime
from itertools import chain
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
    A SeriesValidation validates a DataFrame by selecting a single series from it, and
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


class WarningSeriesGenerator(BaseValidation, abc.ABC):
    """
    Mixin class that indicates that this Validation can produce a "warning series", which is a pandas Series with one
    or more warnings in each cell, corresponding to warnings detected in the DataFrame at the same index
    """

    @abc.abstractmethod
    def get_warning_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Return a series of ValidationWarnings, not an iterable of ValidationWarnings like the normal validate() method
        """

    def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
        warnings = self.get_warning_series(df)
        return warnings.dropna().explode().tolist()


class BooleanSeriesValidation(IndexSeriesValidation, WarningSeriesGenerator):
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

    def get_warning_series(self, series) -> pd.Series:
        """
        Validates a series and returns a series of warnings.
        This is shared by the two validation entrypoints, :py:meth:~validate_with_series, and :py:meth:`~validate_series
        :param series: The series to validate
        """
        failed = ~self.select_cells(series)

        # Slice out the failed items, then map each into a list of validation warnings at each respective index
        return series[failed].to_frame().apply(lambda row: [ValidationWarning(self, {
            'row': row.name,
            'value': row[0]
        })], axis='columns')


class CombinedValidation(WarningSeriesGenerator):
    """
    Validates if one and/or the other validation is true for an element
    """

    def __init__(self, validation_a: BooleanSeriesValidation, validation_b: BooleanSeriesValidation, operator: str,
                 message: str):
        super().__init__(message=message)
        self.operator = operator
        self.left = validation_a
        self.right = validation_b

    def get_warning_series(self, df: pd.DataFrame) -> pd.Series:
        # Let both validations separately select and filter a column
        left_series = self.left.select_series(df)
        right_series = self.right.select_series(df)

        left_errors = self.left.get_warning_series(left_series)
        right_errors = self.right.get_warning_series(right_series)

        if self.operator == 'and':
            # If it's an "and" validation, left, right, or both failing means an error, so we can simply concatenate
            # the lists of errors
            combined = left_errors.combine(right_errors, func=operator.add)
        elif self.operator == 'or':
            # [error] and [] = []
            # [error_1] and [error_2] = [error_2]
            # [] and [] = []
            # Thus, we can use the and operator to implement "or" validations
            combined = left_errors.combine(right_errors, func=operator.and_)#func=lambda a, b: [] if len(a) == 0 or len(b) == 0 else a + b)
        else:
            raise Exception('Operator must be "and" or "or"')

        return combined

    @property
    def default_message(self):
        return '({}) {} ({})'.format(self.v_a.message, self.operator, self.v_b.message)
