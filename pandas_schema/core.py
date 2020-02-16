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

    # def generate_warnings(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
    #     """
    #     Given a series that has been sliced down to only those that definitely failed, produce a list of
    #     ValidationWarnings.
    #     Note, this is different to validate_series, which actually calculates which rows have failed.
    #     Having this as a separate method allows it to be accessed by the CombinedValidation
    #
    #     :param series: A series that has been sliced down to only those that definitely failed
    #     """
    #     return (
    #         ValidationWarning(self, {
    #             'row': row_idx,
    #             'value': cell
    #         }) for row_idx, cell in series.items()
    #     )

    def warning_series(self, series):
        failed = ~self.select_cells(series)

        # Slice out the failed items, then map each into a list of validation warnings at each respective index
        return series[failed].to_frame().apply(lambda row: [ValidationWarning(self, {
                'row': row.name,
                'value': row[0]
            })], axis='columns')

    def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
        warnings = self.warning_series(series)

        # Remove the empty elements, split the list of warnings in each cell, and then compile that into a list
        return warnings.dropna().explode().tolist()


class CombinedValidation(BaseValidation):
    """
    Validates if one and/or the other validation is true for an element
    """

    def __init__(self, validation_a: BooleanSeriesValidation, validation_b: BooleanSeriesValidation, operator,
                 message: str):
        super().__init__(message=message)
        self.operator = operator
        self.left = validation_a
        self.right = validation_b

    def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
        # Let both validations separately select and filter a column
        left_series = self.left.select_series(df)
        right_series = self.right.select_series(df)

        left_errors = self.left.warning_series(left_series)
        right_errors = self.right.warning_series(right_series)

        # TODO

        # Then, we combine the two resulting boolean series, and determine the row indices of the result
        # failed = self.operator(left_errors, right_errors)
        #
        # # If they did fail, obtain warnings from the validation that caused it
        # return chain(
        #     self.v_a.generate_warnings(left_series[left_failed & failed]),
        #     self.v_b.generate_warnings(right_series[right_failed & failed]),
        # )

    @property
    def default_message(self):
        return '({}) {} ({})'.format(self.v_a.message, self.operator, self.v_b.message)
