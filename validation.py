from typing import Callable

import datetime
import pandas as pd
import typing


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

    @property
    def validate(self, series: pd.Series) -> pd.Series:
        return self._validation(series)


class CanCastValidation(Validation):
    def __init__(self, type):
        self.cast_type = type

    def get_message(self, value):
        return 'cannot be cast to type {}'.format(self.cast_type)

    @staticmethod
    def can_cast(var, type):
        try:
            type(var)
            return True
        except:
            return False

    def validate(self, series: pd.Series):
        return series.apply(self.can_cast)


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

    def validate(self, series: pd.Series):
        return series.str.contains(self.pattern)

class TrailingWhitespaceValidation(Validation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self):
        pass

    def get_message(self, value):
        return 'contains trailing whitespace'

    def validate(self, series: pd.Series):
        return ~series.str.contains('\s+$')

class LeadingWhitespaceValidation(Validation):
    """
    Checks that there is no trailing whitespace in this column
    """

    def __init__(self):
        pass

    def get_message(self, value):
        return 'contains leading whitespace'

    def validate(self, series: pd.Series):
        return ~series.str.contains('^\s+')


class InListValidation(Validation):
    """
    Checks that each element in this column is contained within a list of possibilities
    """

    def __init__(self, options: typing.Iterable):
        self.options = options

    def get_message(self, value):
        return 'has a value of "{}" which is not in the list of legal options ("{}")'.format(value, ','.join(self.options))

    def validate(self, series: pd.Series):
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

    def validate(self, series: pd.Series):
        return series.apply(self.valid_date)

