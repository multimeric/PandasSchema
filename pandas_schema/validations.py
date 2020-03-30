import abc
import math
import datetime
import pandas as pd
import numpy as np
import typing
import operator

from . import column
from .core import SeriesValidation, IndexValidation
from .index import DualAxisIndexer
from .validation_warning import ValidationWarning
from .errors import PanSchArgumentError
from pandas.api.types import is_categorical_dtype, is_numeric_dtype
from pandas_schema.scope import ValidationScope


class CustomSeriesValidation(SeriesValidation):
    """
    Validates using a user-provided function that operates on an entire series (for example by using one of the pandas
    Series methods: http://pandas.pydata.org/pandas-docs/stable/api.html#series)
    """

    def __init__(self, validation: typing.Callable[[pd.Series], pd.Series], *args, **kwargs):
        """
        :param message: The error message to provide to the user if this validation fails. The row and column and
            failing value will automatically be prepended to this message, so you only have to provide a message that
            describes what went wrong, for example 'failed my validation' will become

            {row: 1, column: "Column Name"}: "Value" failed my validation
        :param validation: A function that takes a pandas Series and returns a boolean Series, where each cell is equal
            to True if the object passed validation, and False if it failed
        """
        super().__init__(*args, **kwargs)
        self._validation = validation


    def validate_series(self, series: pd.Series) -> pd.Series:
        return self._validation(series)


class CustomElementValidation(SeriesValidation):
    """
    Validates using a user-provided function that operates on each element
    """

    def __init__(self, validation: typing.Callable[[typing.Any], typing.Any], *args, **kwargs):
        """
        :param message: The error message to provide to the user if this validation fails. The row and column and
            failing value will automatically be prepended to this message, so you only have to provide a message that
            describes what went wrong, for example 'failed my validation' will become

            {row: 1, column: "Column Name"}: "Value" failed my validation
        :param validation: A function that takes the value of a data frame cell and returns True if it passes the
            the validation, and false if it doesn't
        """
        self._validation = validation
        super().__init__(*args, **kwargs)

    def validate_series(self, series: pd.Series) -> pd.Series:
        return series.apply(self._validation)


class InRangeValidation(SeriesValidation):
    """
    Checks that each element in the series is within a given numerical range
    """

    def __init__(self, min: float = -math.inf, max: float = math.inf, **kwargs):
        """
        :param min: The minimum (inclusive) value to accept
        :param max: The maximum (exclusive) value to accept
        """
        self.min = min
        self.max = max
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'was not in the range [{}, {})'.format(self.min, self.max)

    def validate_series(self, series: pd.Series) -> pd.Series:
        series = pd.to_numeric(series)
        return (series >= self.min) & (series < self.max)


class IsDtypeValidation(SeriesValidation, scope=ValidationScope.SERIES):
    """
    Checks that a series has a certain numpy dtype
    """

    def __init__(self, dtype: np.dtype, **kwargs):
        """
        :param dtype: The numpy dtype to check the column against
        """
        super().__init__(**kwargs)
        self.dtype = dtype

    def default_message(self, warning: ValidationWarning) -> str:
        return 'has a dtype of {} which is not a subclass of the required type {}'.format(
            self.dtype, warning.props['dtype'])

    def validate_series(self, series: pd.Series):
        if np.issubdtype(series.dtype, self.dtype):
            return True
        else:
            return False
        #     return [ValidationWarning(
        #         self,
        #         {'dtype': series.dtype}
        #     )]
        # else:
        #     return []


class CanCallValidation(SeriesValidation):
    """
    Validates if a given function can be called on each element in a column without raising an exception
    """

    def __init__(self, func: typing.Callable, **kwargs):
        """
        :param func: A python function that will be called with the value of each cell in the DataFrame. If this
            function throws an error, this cell is considered to have failed the validation. Otherwise it has passed.
        """
        if callable(type):
            self.callable = func
        else:
            raise PanSchArgumentError(
                'The object "{}" passed to CanCallValidation is not callable!'.format(
                    type))
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'raised an exception when the callable {} was called on it'.format(
            self.callable)

    def can_call(self, var):
        try:
            self.callable(var)
            return True
        except:
            return False

    def validate_series(self, series: pd.Series) -> pd.Series:
        return series.apply(self.can_call)


class CanConvertValidation(CanCallValidation):
    """
    Checks if each element in a column can be converted to a Python object type
    """

    """
    Internally this uses the same logic as CanCallValidation since all types are callable in python.
    However this class overrides the error messages to make them more directed towards types
    """

    def __init__(self, _type: type, **kwargs):
        """
        :param _type: Any python type. Its constructor will be called with the value of the individual cell as its
            only argument. If it throws an exception, the value is considered to fail the validation, otherwise it has passed
        """
        if isinstance(_type, type):
            super(CanConvertValidation, self).__init__(_type, **kwargs)
        else:
            raise PanSchArgumentError('{} is not a valid type'.format(_type))

    def default_message(self, warning: ValidationWarning):
        return 'cannot be converted to type {}'.format(self.callable)


class MatchesPatternValidation(SeriesValidation):
    """
    Validates that a string or regular expression can match somewhere in each element in this column
    """

    def __init__(self, pattern, options={}, **kwargs):
        """
        :param kwargs: Arguments to pass to Series.str.contains
            (http://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.str.contains.html)
            pat is the only required argument
        """
        self.pattern = pattern
        self.options = options
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'does not match the pattern "{}"'.format(self.pattern.pattern)

    def validate_series(self, series: pd.Series) -> pd.Series:
        return series.astype(str).str.contains(self.pattern, **self.options)


class TrailingWhitespaceValidation(SeriesValidation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'contains trailing whitespace'

    def validate_series(self, series: pd.Series) -> pd.Series:
        return ~series.astype(str).str.contains('\s+$')


class LeadingWhitespaceValidation(SeriesValidation):
    """
    Checks that there is no leading whitespace in this column
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'contains leading whitespace'

    def validate_series(self, series: pd.Series) -> pd.Series:
        return ~series.astype(str).str.contains('^\s+')


class IsDistinctValidation(SeriesValidation):
    """
    Checks that every element of this column is different from each other element
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'contains values that are not unique'

    def validate_series(self, series: pd.Series) -> pd.Series:
        return ~series.duplicated(keep='first')


class InListValidation(SeriesValidation):
    """
    Checks that each element in this column is contained within a list of possibilities
    """

    def __init__(self, options: typing.Iterable, case_sensitive: bool = True, **kwargs):
        """
        :param options: A list of values to check. If the value of a cell is in this list, it is considered to pass the
            validation
        """
        self.case_sensitive = case_sensitive
        self.options = options
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        values = ', '.join(str(v) for v in self.options)
        return 'is not in the list of legal options ({})'.format(values)

    def validate_series(self, series: pd.Series) -> pd.Series:
        if self.case_sensitive:
            return series.isin(self.options)
        else:
            return series.str.lower().isin([s.lower() for s in self.options])


class DateFormatValidation(SeriesValidation):
    """
    Checks that each element in this column is a valid date according to a provided format string
    """

    def __init__(self, date_format: str, **kwargs):
        """
        :param date_format: The date format string to validate the column against. Refer to the date format code
            documentation at https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior for a full
            list of format codes
        """
        self.date_format = date_format
        super().__init__(**kwargs)

    def default_message(self, warning: ValidationWarning):
        return 'does not match the date format string "{}"'.format(self.date_format)

    def valid_date(self, val):
        try:
            datetime.datetime.strptime(val, self.date_format)
            return True
        except:
            return False

    def validate_series(self, series: pd.Series) -> pd.Series:
        return series.astype(str).apply(self.valid_date)
