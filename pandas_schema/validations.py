from .core import SeriesValidation, IndexSeriesValidation, BooleanSeriesValidation
from .validation_warning import ValidationWarning
from .errors import PanSchError, PanSchArgumentError
import numpy as np
import pandas as pd
import math
import typing
import datetime


class IsDtypeValidation(IndexSeriesValidation):
    """
    Checks that a series has a certain numpy dtype
    """

    def __init__(self, dtype: np.dtype, **kwargs):
        """
        :param dtype: The numpy dtype to check the column against
        """
        self.dtype = dtype
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'did not have the dtype "{}"'.format(self.dtype.name)

    def validate_series(self, series: pd.Series):
        if not series.dtype == self.dtype:
            return [self.Warning(self, self.message, series, self.index, self.positional)]


class InRangeValidation(BooleanSeriesValidation):
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

    def select_cells(self, series: pd.Series) -> pd.Series:
        series = pd.to_numeric(series)
        return (series >= self.min) & (series < self.max)

    @property
    def default_message(self):
        return 'was not in the range [{}, {})'.format(self.min, self.max)


class CanCallValidation(BooleanSeriesValidation):
    """
    Validates if a given function can be called on each element in a column without raising an exception
    """

    def select_cells(self, series: pd.Series) -> pd.Series:
        return series.apply(self.can_call)

    def __init__(self, func: typing.Callable, **kwargs):
        """
        :param func: A python function that will be called with the value of each cell in the DataFrame. If this
            function throws an error, this cell is considered to have failed the validation. Otherwise it has passed.
        """
        if callable(type):
            self.callable = func
        else:
            raise PanSchArgumentError('The object "{}" passed to CanCallValidation is not callable!'.format(type))
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'raised an exception when the callable {} was called on it'.format(self.callable)

    def can_call(self, var):
        try:
            self.callable(var)
            return True
        except:
            return False


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

    @property
    def default_message(self):
        return 'cannot be converted to type {}'.format(self.callable)


class MatchesPatternValidation(BooleanSeriesValidation):
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

    @property
    def default_message(self):
        return 'does not match the pattern "{}"'.format(self.pattern)

    def select_cells(self, series: pd.Series) -> pd.Series:
        return series.astype(str).str.contains(self.pattern, **self.options)


class TrailingWhitespaceValidation(BooleanSeriesValidation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'contains trailing whitespace'

    def select_cells(self, series: pd.Series) -> pd.Series:
        return ~series.astype(str).str.contains('\s+$')


class LeadingWhitespaceValidation(BooleanSeriesValidation):
    """
    Checks that there is no leading whitespace in this column
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'contains leading whitespace'

    def select_cells(self, series: pd.Series) -> pd.Series:
        return ~series.astype(str).str.contains('^\s+')


class IsDistinctValidation(BooleanSeriesValidation):
    """
    Checks that every element of this column is different from each other element
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def default_message(self):
        return 'contains values that are not unique'

    def select_cells(self, series: pd.Series) -> pd.Series:
        return ~series.duplicated(keep='first')


class InListValidation(BooleanSeriesValidation):
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

    @property
    def default_message(self):
        values = ', '.join(str(v) for v in self.options)
        return 'is not in the list of legal options ({})'.format(values)

    def select_cells(self, series: pd.Series) -> pd.Series:
        if self.case_sensitive:
            return series.isin(self.options)
        else:
            return series.str.lower().isin([s.lower() for s in self.options])


class DateFormatValidation(BooleanSeriesValidation):
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

    @property
    def default_message(self):
        return 'does not match the date format string "{}"'.format(self.date_format)

    def valid_date(self, val):
        try:
            datetime.datetime.strptime(val, self.date_format)
            return True
        except:
            return False

    def select_cells(self, series: pd.Series) -> pd.Series:
        return series.astype(str).apply(self.valid_date)
