import abc
import math
import datetime
from itertools import chain
import pandas as pd
import numpy as np
import typing
import operator
from dataclasses import dataclass
import enum
import copy
from math import isnan

from .errors import PanSchArgumentError, PanSchNoIndexError
from pandas_schema.validation_warning import ValidationWarning, CombinedValidationWarning
from pandas_schema.index import AxisIndexer, IndexValue, IndexType, RowIndexer, \
    DualAxisIndexer, BooleanIndexer
from pandas_schema.scope import ValidationScope
from pandas.api.types import is_categorical_dtype, is_numeric_dtype

SubSelection = typing.Union[pd.Series, pd.DataFrame, object]
"""
Anything that an indexer could return from a DataFrame
"""


class BaseValidation(abc.ABC):
    """
    A validation is, broadly, just a function that maps a data frame to a list of errors
    """

    def __init_subclass__(cls, scope: ValidationScope = ValidationScope.CELL, **kwargs):
        # We override this so that you can set the scope at the time you declare the validation class, not the instance
        cls.scope = scope

    def __init__(self, message: str = None):
        """
        Creates a new IndexSeriesValidation
        :param message: A custom message to use for ValidationWarnings generated by this validation
        """
        self.custom_message = message

    def recurse(self, func: typing.Callable[['BaseValidation'], typing.Any]) -> list:
        """
        Calls a function on this validation and all of its children (if this is a compound validation)
        Args:
            func: A function whose only argument is a single validation. The function might change the validation, or
            if can return a value, in which case the value will be included in the final result

        Returns:
            A list of result values

        """
        return [func(self)]

    def map(self, func: typing.Callable[['BaseValidation'], 'BaseValidation']) -> 'BaseValidation':
        """
        Calls a function on this validation and all of its children (if this is a compound validation)
        This function return a validation that will replace the validation it receives as an argument.
        Args:
            func: A function whose only argument is a single validation. The function might change the validation, or
            if can return a value, in which case the value will be included in the final result

        Returns:
            A list of result values

        """
        return func(self)

    def make_df_warning(self, df: pd.DataFrame) -> ValidationWarning:
        """
        Creates a DF-scope warning. Can be overridden by child classes
        """
        return ValidationWarning(self)

    def make_row_warning(self, df: pd.DataFrame, row_index: IndexValue) -> ValidationWarning:
        """
        Creates a series-scope warning. Can be overridden by child classes
        """
        return ValidationWarning(self, row=row_index)

    def make_series_warning(self, df: pd.DataFrame, column: str,
                            series: pd.Series) -> ValidationWarning:
        """
        Creates a series-scope warning. Can be overridden by child classes
        """
        return ValidationWarning(self, column=column)

    def make_cell_warning(self, df: pd.DataFrame, column: str, row: int, value,
                          series: pd.Series = None) -> ValidationWarning:
        """
        Creates a cell-scope warning. Can be overridden by child classes
        """
        return ValidationWarning(self, column=column, row=row, value=value)

    def index_to_warnings_series(self, df: pd.DataFrame, index: DualAxisIndexer, failed: SubSelection):
        """
        Takes an index that points to parts of the DF that have *failed* validation, and returns a Series (or similar)
        that has ValidationWarning instances at each index that has failed
        :param df: The DataFrame we're validating
        :param index: The index pointing to the failed parts of the DF
        :param failed: The result of applying index to the DF
        """

        # If it's am empty series/frame then this produced no warnings
        if isinstance(failed, (pd.DataFrame, pd.Series)) and failed.empty:
            return pd.Series()

        # Depending on the scope, we produce the lists of warnings in different ways (ideally the most efficient ways)
        if isinstance(failed, pd.DataFrame):
            if self.scope == ValidationScope.DATA_FRAME:
                return [self.make_df_warning(df)]
            elif self.scope == ValidationScope.SERIES:
                return failed.apply(lambda series: self.make_series_warning(
                    df=df,
                    column=series.name,
                    series=series
                ), axis='rows')
            elif self.scope == ValidationScope.ROW:
                return failed.apply(lambda row: self.make_row_warning(
                    df=df,
                    row_index=row.name
                ), axis='columns')
            elif self.scope == ValidationScope.CELL:
                return failed.apply(lambda series: series.to_frame().apply(
                    lambda cell: self.make_cell_warning(
                        df=df,
                        column=series.name,
                        series=series,
                        row=cell.name,
                        value=cell
                    )))
        elif isinstance(failed, pd.Series):
            if self.scope == ValidationScope.SERIES:
                return [self.make_series_warning(
                    df=df,
                    column=failed.name,
                    series=failed
                )]
            elif self.scope == ValidationScope.CELL:
                # DataFrame.apply returns a series if the function returns a scalar, as it does here
                return failed.to_frame().apply(lambda cell: self.make_cell_warning(
                    df=df,
                    column=index.col_index.index,
                    series=failed,
                    row=cell.name,
                    value=cell[0]
                ), axis='columns')
        else:
            return [self.make_cell_warning(
                df=df,
                column=index.col_index.index,
                row=index.row_index.index,
                value=failed)
            ]

    def get_warnings_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Converts an index into a series of warnings each corresponding to an issue
        with the DataFrame at the same index.
        """
        index = self.get_failed_index(df)
        failed = index(df)

        return self.index_to_warnings_series(df, index, failed)

    @staticmethod
    def to_warning_list(failed: SubSelection):
        """
        Converts a Series/DF of warnings to a list of warnings
        """
        if isinstance(failed, pd.DataFrame):
            return failed.to_numpy().tolist()
        elif isinstance(failed, pd.Series):
            return failed.tolist()
        else:
            return failed

    def validate(self, df: pd.DataFrame) -> typing.Collection[ValidationWarning]:
        """
        Validates a data frame and returns a list of issues with it
        :param df: Data frame to validate
        :return: All validation failures detected by this validation
        """
        failed = self.get_warnings_series(df)
        return self.to_warning_list(failed)

    @abc.abstractmethod
    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        """
        Returns an indexer object that fully specifies which sections of the DataFrame this validation believes are
        invalid (both row and column-wise)
        """

    @abc.abstractmethod
    def get_failed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        """
        Returns an indexer object that fully specifies which sections of the DataFrame this validation believes are
        valid (both row and column-wise)
        """

    def message(self, warning: ValidationWarning) -> str:
        """
        Get a string that fully describes the provided warning, given that the warning was generating by this validation
        """
        return "{} {}".format(self.prefix(warning), self.suffix(warning))

    def prefix(self, warning: ValidationWarning):
        """
        Return a string that can be used to prefix a message that relates to this index

        This method is safe to override
        """
        return ""

    def suffix(self, warning: ValidationWarning):
        # The suffix can be overridden in two ways, either using a custom message (the most common), or with a custom
        # default_message() function
        if self.custom_message:
            return self.custom_message
        else:
            return self.default_message(warning)

    @property
    def readable_name(self):
        """
        A readable name for this validation, to be shown in validation warnings
        """
        return type(self).__name__

    def default_message(self, warning: ValidationWarning) -> str:
        """
        Returns a description of this validation, to be included in the py:meth:~message as the suffix``
        """
        return 'failed the {}'.format(self.readable_name)

    def __or__(self, other: 'BaseValidation'):
        """
        Returns a validation that will only return an error if both validations fail at the same place
        :param other: Another validation to combine with this
        """
        if not isinstance(other, BaseValidation):
            raise PanSchArgumentError('The "|" operator can only be used between two'
                                      'Validations that subclass {}'.format(
                self.__class__))

        # TODO: Propagate the individual validator indexes when we And/Or them together
        return CombinedValidation(self, other, operator=operator.or_)

    def __and__(self, other: 'BaseValidation'):
        """
        Returns a validation that will only return an error if both validations fail at the same place
        :param other: Another validation to combine with this
        """
        if not isinstance(other, BaseValidation):
            raise PanSchArgumentError('The "&" operator can only be used between two'
                                      'Validations that subclass {}'.format(
                self.__class__))

        # TODO: Propagate the individual validator indexes when we And/Or them together
        return CombinedValidation(self, other, operator=operator.and_)


class IndexValidation(BaseValidation):
    """
    An IndexValidation expands upon a BaseValidation by adding an index (in Pandas co-ordinates) that points to the
    Series/DF sub-selection/row/cell that it validates
    """

    def __init__(
            self,
            index: DualAxisIndexer,
            *args,
            **kwargs
    ):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
            Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        super().__init__(*args, **kwargs)
        self.index = index

    def apply_index(self, df: pd.DataFrame) -> SubSelection:
        """
        Select a series using the data stored in this validation
        """
        return self.index(df)

    def prefix(self, warning: ValidationWarning):
        ret = []

        if self.index.col_index is not None:
            col_str = self.index.col_index.for_message()
            if col_str:
                ret.append(col_str)

        ret.append('Row {}'.format(warning.props['row']))

        ret.append('Value "{}"'.format(warning.props['value']))

        return '{' + ', '.join(ret) + '}'

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        selection = self.apply_index(df)
        return self.validate_selection(selection)

    @abc.abstractmethod
    def validate_selection(self, selection: SubSelection) -> DualAxisIndexer:
        """
        Given a selection, return an indexer that points to elements that passed the validation
        """
        pass

    def optional(self) -> 'CombinedValidation':
        """
        Makes this Validation optional, by returning a CombinedValidation that accepts empty cells
        """
        return CombinedValidation(
            self,
            IsEmptyValidation(index=self.index),
            operator=operator.or_
        )


class SeriesValidation(IndexValidation):
    """
    A type of IndexValidation that expands IndexValidation with the knowledge that it will validate a single Series
    """
    _index: typing.Optional[DualAxisIndexer]

    def __init__(self, index: typing.Union[RowIndexer, IndexValue, DualAxisIndexer] = None, negated: bool=False, *args, **kwargs):
        """
        Create a new SeriesValidation
        :param index: The index pointing to the Series to validate. For example, this might be 2 to validate Series
            with index 2, or "first_name" to validate a Series named "first_name". For more advanced indexing, you may
            pass in an instance of the RowIndexer class
        """
        # This convets the index from primitive numbers into a data structure
        self._index = None
        self.index = index

        super().__init__(
            *args,
            index=self.index,
            **kwargs
        )

        self.negated = negated
        """
        This broadly means that this validation will do the opposite of what it normally does. The actual implementation
        depends on the subclass checking for this field whenever it needs to. Even for IndexValidations, we can't invert
        the actual index, because it doesn't exist yet. It's only created after we run the actual validation
        """

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, val):
        # We have to convert a single-axis index into a dual-axis index
        if val is not None:
            if isinstance(val, DualAxisIndexer):
                self._index = val
            else:
                self._index = DualAxisIndexer(
                    col_index=val,
                    row_index=BooleanIndexer(index=True, axis=0),
                )

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        index = super().get_passed_index(df)
        if self.negated:
            return index.invert(axis=0)
        else:
            return index

    def get_failed_index(self, df) -> DualAxisIndexer:
        # This is the opposite of get_passed_index, so we just flip the conditional
        index = super().get_passed_index(df)
        if self.negated:
            return index
        else:
            return index.invert(axis=0)

    def validate_selection(self, selection: SubSelection) -> DualAxisIndexer:
        """
        Since this is a SeriesValidation, we can simplify the validation. Now we only have to ask the subclass to take
        a Series and return a Series (or slice) that indicates the successful cells (or series). Then we can combine
        this with the current index to produce an indexer that finds all failing cells in the DF
        """
        row_index = self.validate_series(selection)

        # As a convenience, we allow validate_series to return a boolean. If True it indicates everything passed, so
        # convert it to a None slice which returns everything, and if false convert it to an empty list, an indexer
        # that returns nothing
        # if isinstance(row_index, bool):
        #     if row_index:
        #         row_index = slice(None)
        #     else:
        #         row_index = []

        return DualAxisIndexer(
            row_index=BooleanIndexer(row_index, axis=0),
            col_index=self.index.col_index
        )

    @abc.abstractmethod
    def validate_series(self, series: pd.Series) -> IndexValue:
        """
        Given a series, return a bool Series that has values of True if the series
            passes the validation, otherwise False
        """

    def __invert__(self) -> 'BaseValidation':
        """
        Returns: A copy of this validation, but that validates the opposite of what it normally would
        """
        clone = copy.copy(self)
        clone.negated = True
        return clone


class CombinedValidation(BaseValidation):
    """
    Validates if one and/or the other validation is true for an element
    """

    def __init__(
            self,
            validation_a: BaseValidation,
            validation_b: BaseValidation,
            operator: typing.Callable[[pd.Series, pd.Series], pd.Series],
            axis='rows'
    ):
        """
        Creates a new CombinedValidation
        :param validation_a: The first validation to combine
        :param validation_b: The second validation to combine
        :param operator: An operator, likely operator.or_ or operator.and_ that we should use to combine Validations
        :param axis: The axis across which to combine validations. If this is "rows", then we keep the column indices
            of each result, and combine the row indices (the most common option). If this is "columns", do the opposite
        """
        super().__init__()
        self.operator = operator
        self.left = validation_a
        self.right = validation_b
        self.axis = axis

    def recurse(self, func: typing.Callable[['BaseValidation'], typing.Any]) -> list:
        return [*super().recurse(func), *self.left.recurse(func), *self.right.recurse(func)]

    def map(self, func):
        new = func(self)
        new.left = new.left.map(func)
        new.right = new.right.map(func)
        return new

    # def message(self, warning: ValidationWarning) -> str:
    #     # Nothing should ever try to create a ValidationWarning directly from a CombinedValidation,
    #     # it should always use the original warnings from the child Validations
    #     raise NotImplementedError()

    # def index_to_warnings_series(self, df: pd.DataFrame, index: DualAxisIndexer, failed: SubSelection):
    #     # We handle this method by deferring to the children

    def combine_indices(self, left: DualAxisIndexer, right: DualAxisIndexer) -> DualAxisIndexer:
        """
        Utility method for combining two indexers using boolean logic
        """
        # TODO: convert axis into an integer and apply proper pandas logic
        if self.axis == 'rows':
            assert left.col_index == right.col_index
            assert isinstance(left.row_index, BooleanIndexer)
            return DualAxisIndexer(
                row_index=BooleanIndexer(self.operator(
                    left.row_index.index,
                    right.row_index.index
                ), axis=0),
                col_index=left.col_index
            )

        elif self.axis == 'columns':
            assert left.row_index == right.row_index
            assert isinstance(left.col_index, BooleanIndexer)
            return DualAxisIndexer(
                row_index=left.row_index,
                col_index=BooleanIndexer(self.operator(
                    left.col_index.index,
                    right.col_index.index
                ), axis=1)
            )

        else:
            raise Exception()

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        left_passed = self.left.get_passed_index(df)
        right_passed = self.right.get_passed_index(df)
        return self.combine_indices(left_passed, right_passed)

    def get_failed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        return self.get_passed_index(df).invert(self.axis)

    def index_to_warnings_series(self, df: pd.DataFrame, index: DualAxisIndexer, failed: SubSelection):
        # In a normal validation this method would create new Validatations, and use the index, but we don't actually
        # need either here
        return self.get_warnings_series(df)

    def combine(self, left: SubSelection, right: SubSelection):
        """
        Combine two subsections of the DataFrame, each containing :py:class:`pandas_schema.validation_warning.ValidationWarning`
        instances
        """

        # Convert the data into warnings, and then join together the warnings from both validations
        def combine_index(left, right):
            # Make a CombinedValidationWarning if it failed both validations, otherwise return the single failure
            if left:
                if right:
                    return CombinedValidationWarning(left, right, validation=self)
                else:
                    return left
            else:
                return right

        if isinstance(left, (pd.Series, pd.DataFrame)):
            return left.combine(right, combine_index, fill_value=False)
        elif isinstance(right, (pd.Series, pd.DataFrame)):
            return right.combine(left, combine_index, fill_value=False)
        else:
            return combine_index(left, right)

    def get_warnings_series(self, df: pd.DataFrame) -> pd.Series:
        # Let both validations separately select and filter a column
        left_index = self.left.get_passed_index(df)
        right_index = self.right.get_passed_index(df)

        # Combine them with boolean logic
        # We have to invert the combined index because left and right are *passed* indices not failed ones
        combined = self.combine_indices(left_index, right_index).invert(axis=0)

        # Slice out the failed data
        # We have to invert these because left_index and right_index are passed indices
        left_failed = left_index.invert(axis=0)(df)
        right_failed = right_index.invert(axis=0)(df)

        warnings = self.combine(
            self.left.index_to_warnings_series(df, left_index, left_failed),
            self.right.index_to_warnings_series(df, right_index, right_failed)
        )
        # warnings = self.left.index_to_warnings_series(df, left_index, left_failed).combine(
        #     self.right.index_to_warnings_series(df, right_index, right_failed),
        #     func=combine,
        #     fill_value=False
        # )

        # Finally, apply the combined index from above to the warnings series
        if self.axis == 'rows':
            return warnings[combined.row_index.index]
        else:
            return warnings[combined.col_index.index]


class IsEmptyValidation(SeriesValidation):
    """
    Validates that each element in the Series is "empty". For most dtypes, this means each element contains null,
    but for strings we consider 0-length strings to be empty
    """

    def validate_series(self, series: pd.Series) -> IndexValue:
        if is_categorical_dtype(series) or is_numeric_dtype(series):
            return series.isnull()
        else:
            return series.str.len() == 0
