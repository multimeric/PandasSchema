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
from pandas_schema.index import PandasIndexer, IndexValue, IndexType
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

    @abc.abstractmethod
    def message(self, warning: ValidationWarning) -> str:
        pass


class IndexValidation(BaseValidation, metaclass=abc.ABCMeta):
    """
    Abstract class that builds on BaseValidation to give it access to an index for selecting a Series out of the
    DataFrame
    """

    def __init__(self, index: typing.Union[PandasIndexer, IndexValue], message: str = None, **kwargs):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
        Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        super().__init__(**kwargs)
        if isinstance(index, PandasIndexer):
            self.index = index
        else:
            # If it isn't already an indexer object, convert it to one
            self.index = PandasIndexer(index=index)
        self.custom_message = message

    def message(self, warning: ValidationWarning) -> str:
        prefix = self.prefix(warning)

        if self.custom_message:
            suffix = self.custom_message
        else:
            suffix = self.default_message(warning)

        return "{} {}".format(prefix, suffix)

    @property
    def readable_name(self, **kwargs):
        """
        A readable name for this validation, to be shown in validation warnings
        """
        return type(self).__name__

    def default_message(self, warnings: ValidationWarning) -> str:
        return 'failed the {}'.format(self.readable_name)

    def select_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Select a series using the data stored in this validation
        """
        if self.index is None:
            raise PanSchNoIndexError()

        return self.index(df)

    def prefix(self, warning: ValidationWarning):
        """
        Return a string that can be used to prefix a message that relates to this index

        This method is safe to override
        """
        if self.index is None:
            return ""

        if self.index.type == IndexType.POSITION:
            return 'Column {}'.format(self.index.index)
        else:
            return 'Column "{}"'.format(self.index.index)


#
# class SeriesValidation(BaseValidation):
#     """
#     A SeriesValidation validates a DataFrame by selecting a single series from it, and
#     applying some validation to it
#     """
#
#     @abc.abstractmethod
#     def select_series(self, df: pd.DataFrame) -> pd.Series:
#         """
#         Selects a series from the DataFrame that will be validated
#         """
#
#     @abc.abstractmethod
#     def validate_series(self, series: pd.Series) -> typing.Iterable[ValidationWarning]:
#         """
#         Validate a single series
#         """
#
#     def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
#         series = self.select_series(df)
#         return self.validate_series(series)


class SeriesValidation(IndexValidation):
    """
    A SeriesValidation validates a DataFrame by selecting a single series from it, and
    applying some validation to it
    """

    def validate(self, df: pd.DataFrame) -> typing.Iterable[ValidationWarning]:
        series = self.index(df)
        return self.validate_series(series)

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

    @staticmethod
    def flatten_warning_series(warnings: pd.Series):
        """
        Converts a warning series into an iterable of warnings
        """
        return warnings[warnings.astype(bool)].explode().tolist()

    def validate(self, df: pd.DataFrame, flatten=True) -> typing.Union[
        typing.Iterable[ValidationWarning],
        pd.Series
    ]:
        warnings = self.get_warning_series(df)
        if flatten:
            return self.flatten_warning_series(warnings)
        else:
            return warnings

    def __or__(self, other: 'WarningSeriesGenerator'):
        if not isinstance(other, WarningSeriesGenerator):
            raise PanSchArgumentError('The "|" operator can only be used between two'
            'Validations that subclass {}'.format(self.__class__))

        return CombinedValidation(self, other, operator='or')



class BooleanSeriesValidation(IndexValidation, WarningSeriesGenerator):
    """
    Validation is defined by the function :py:meth:~select_cells that returns a boolean series.
        Each cell that has False has failed the validation.

        Child classes need not create their own :py:class:~pandas_schema.core.BooleanSeriesValidation.Warning subclass,
        because the data is in the same form for each cell. You need only define a :py:meth~default_message.
    """

    def __init__(self, *args, negated=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.negated = negated

    @abc.abstractmethod
    def select_cells(self, series: pd.Series) -> pd.Series:
        """
        A BooleanSeriesValidation must return a boolean series. Each cell that has False has failed the
            validation
        :param series: The series to validate
        """
        pass

    def validate_series(self, series, flatten=True) -> typing.Union[
        typing.Iterable[ValidationWarning],
        pd.Series
    ]:
        """
        Validates a single series selected from the DataFrame
        """
        selection = self.select_cells(series)

        if self.negated:
            # If self.negated (which is not the default), then we don't need to flip the booleans
            failed = selection
        else:
            # In the normal case we do need to flip the booleans, since select_cells returns True for cells that pass
            # the validation, and we want cells that failed it
            failed = ~selection

        # Slice out the failed items, then map each into a list of validation warnings at each respective index
        warnings = series[failed].to_frame().apply(lambda row: [ValidationWarning(self, {
            'row': row.name,
            'value': row[0]
        })], axis='columns', result_type='reduce')
        # warnings = warnings.iloc[:, 0]

        # If flatten, return a list of ValidationWarning, otherwise return a series of lists of Validation Warnings
        if flatten:
            return self.flatten_warning_series(warnings)
        else:
            return warnings

    def get_warning_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Validates a series and returns a series of warnings.
        """
        series = self.select_series(df)
        return self.validate_series(series, flatten=False)

    def prefix(self, warning: ValidationWarning):
        parent = super().prefix(warning)
        # Only in this subclass do we know the contents of the warning props, since we defined them in the
        # validate_series method. Thus, we can now add row index information

        return parent + ', Row {row}: "{value}"'.format(**warning.props)

    def __invert__(self) -> 'BooleanSeriesValidation':
        """
        If a BooleanSeriesValidation is negated, it has the opposite result
        """
        self.negated = not self.negated
        return self


class CombinedValidation(WarningSeriesGenerator):
    """
    Validates if one and/or the other validation is true for an element
    """

    def message(self, warning: ValidationWarning) -> str:
        pass

    def __init__(self, validation_a: WarningSeriesGenerator, validation_b: WarningSeriesGenerator, operator: str):
        super().__init__()
        self.operator = operator
        self.left = validation_a
        self.right = validation_b

    def get_warning_series(self, df: pd.DataFrame) -> pd.Series:
        # Let both validations separately select and filter a column
        left_errors = self.left.validate(df, flatten=False)
        right_errors = self.right.validate(df, flatten=False)

        if self.operator == 'and':
            # If it's an "and" validation, left, right, or both failing means an error, so we can simply concatenate
            # the lists of errors
            combined = left_errors.combine(right_errors, func=operator.add, fill_value=[])
        elif self.operator == 'or':
            # [error] and [] = []
            # [error_1] and [error_2] = [error_2]
            # [] and [] = []
            # Thus, we can use the and operator to implement "or" validations
            combined = left_errors.combine(right_errors, func=lambda l, r: l + r if l and r else [], fill_value=[])
            # func=lambda a, b: [] if len(a) == 0 or len(b) == 0 else a + b)
        else:
            raise Exception('Operator must be "and" or "or"')

        return combined

    @property
    def default_message(self, warnings: ValidationWarning) -> str:
        return '({}) {} ({})'.format(self.v_a.message, self.operator, self.v_b.message)
