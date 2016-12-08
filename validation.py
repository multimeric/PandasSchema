from typing import Callable

import datetime
import pandas as pd
import typing

from errors import PanSchArgumentError


class Validation:
    """
    An object used to validate against a single cell of a data frame
    """

    def __init__(self, message: str = None, validation: Callable[[pd.Series], pd.Series] = None):
        """
        Creates a new validation object
        :param message: The error message to provide to the user if this validation fails
        :param validation: A function that takes a pandas series and returns a boolean series, where the cell is equal to
        True if the object passed validation, and False if it failed
        """
        self._message = message
        self._validation = validation

    def get_message(self, value):
        return self._message

    def validate(self, series: pd.Series) -> pd.Series:
        return self._validation(series)


class CanCallValidation(Validation):
    """
    Validates if a given function can be called on each element in a column without raising an exception
    """

    def __init__(self, func):
        if callable(type):
            self.callable = func
        else:
            raise PanSchArgumentError('The object "{}" passed to CanCallValidation is not callable!'.format(type))

    def get_message(self, value):
        return 'raised an exception when the callable {} was called on it'.format(self.callable)

    def can_call(self, var):
        try:
            self.callable(var)
            return True
        except:
            return False

    def validate(self, series: pd.Series) -> pd.Series:
        return series.apply(self.can_call)


class CanConvertValidation(CanCallValidation):
    """
    Checks if each element in a column can be converted to a Python object type
    """

    """
    Internally this uses the same logic as CanCallValidation since all types are callable in python.
    However this class overrides the error messages to make them more directed towards types
    """

    def __init__(self, _type):
        if isinstance(_type, type):
            super(CanConvertValidation, self).__init__(_type)
        else:
            raise PanSchArgumentError('{} is not a valid type'.format(_type))

    def get_message(self, value):
        return 'cannot be converted to type {}'.format(self.callable)



class MatchesRegexValidation(Validation):
    """
    Validates that a regular expression can match somewhere in each element in this column
    """

    def __init__(self, regex: typing.re.Pattern):
        """
        :param regex: A regular expression object, created using re.compile or similar
        """

        self.pattern = regex

    def get_message(self, value):
        return 'does not match the regex {}'.format(self.pattern)

    def validate(self, series: pd.Series) -> pd.Series:
        return series.str.contains(self.pattern)


class TrailingWhitespaceValidation(Validation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self):
        pass

    def get_message(self, value):
        return 'contains trailing whitespace'

    def validate(self, series: pd.Series) -> pd.Series:
        return ~series.str.contains('\s+$')


class LeadingWhitespaceValidation(Validation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self):
        pass

    def get_message(self, value):
        return 'contains leading whitespace'

    def validate(self, series: pd.Series) -> pd.Series:
        return ~series.str.contains('^\s+')


class InListValidation(Validation):
    """
    Checks that each element in this column is contained within a list of possibilities
    """

    def __init__(self, options: typing.Iterable):
        self.options = options

    def get_message(self, value):
        return 'has a value of "{}" which is not in the list of legal options ("{}")'.format(value,
                                                                                             ','.join(self.options))

    def validate(self, series: pd.Series) -> pd.Series:
        return series.isin(self.options)


class DateFormatValidation(Validation):
    """
    Checks that each element in this column is a valid date according to a provided format string
    """

    def __init__(self, date_format: str):
        self.date_format = date_format

    def get_message(self, value):
        return 'has a value of "{}", which does not match the date format string "{}"'.format(value, self.date_format)

    def valid_date(self, val):
        try:
            datetime.datetime.strptime(val, self.date_format)
            return True
        except:
            return False

    def validate(self, series: pd.Series) -> pd.Series:
        return series.apply(self.valid_date)
