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

from . import column
from .errors import PanSchArgumentError, PanSchNoIndexError
from pandas_schema.validation_warning import ValidationWarning
from pandas_schema.index import AxisIndexer, IndexValue, IndexType, RowIndexer, \
    DualAxisIndexer
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
        cls.scope = scope

    def __init__(self, message: str = None, negated: bool = False):
        """
        Creates a new IndexSeriesValidation
        :param index: An index with which to select the series
            Otherwise it's a label (ie, index=0) indicates the column with the label of 0
        """
        self.custom_message = message
        self.negated = negated

    def make_df_warning(self, df: pd.DataFrame) -> ValidationWarning:
        """
        Creates a DF-scope warning. Can be overridden by child classes
        """
        return ValidationWarning(self)

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

    def apply_negation(self, index: DualAxisIndexer) -> DualAxisIndexer:
        """
        Can be implemented by sub-classes to provide negation behaviour. If implemented, this should return a new
        indexer that returns the opposite of what it normally would. The definition of opposite may vary from validation
        to validation
        """
        raise NotImplementedError()

    def index_to_warnings_series(self, df: pd.DataFrame, index: DualAxisIndexer, failed):

        # If it's am empty series/frame then this produced no warnings
        if isinstance(failed, (pd.DataFrame, pd.Series)) and failed.empty:
            return []

        # Depending on the scope, we produce the lists of warnings in different ways
        if isinstance(failed, pd.DataFrame):
            if self.scope == ValidationScope.DATA_FRAME:
                return [self.make_df_warning(df)]
            elif self.scope == ValidationScope.SERIES:
                return df.apply(lambda series: self.make_series_warning(
                    df=df,
                    column=series.name,
                    series=series
                ), axis=0)
            elif self.scope == ValidationScope.CELL:
                return df.apply(lambda series: series.to_frame().apply(
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
                    column=index.col_index.index,
                    series=failed
                )]
            elif self.scope == ValidationScope.CELL:
                return failed.to_frame().apply(lambda cell: self.make_cell_warning(
                    df=df,
                    column=index.col_index.index,
                    series=failed,
                    row=cell.name,
                    value=cell[0]
                ), axis=1)
        else:
            return [self.make_cell_warning(
                df=df,
                column=self.index.col_index.index,
                row=self.index.row_index.index,
                value=failed)
            ]

    def get_warnings_series(self, df: pd.DataFrame) -> pd.Series:
        """
        Converts an index into a series of warnings each corresponding to an issue
        with the DataFrame at the same index.
        """
        index = self.get_failed_index(df)
        if self.negated:
            index = self.apply_negation(index)
        failed = index(df)

        return self.index_to_warnings_series(df, index, failed)

    @staticmethod
    def to_warning_list(failed):
        if isinstance(failed, pd.DataFrame):
            return failed.to_numpy().tolist()
        elif isinstance(failed, pd.Series):
            return failed.tolist()
        else:
            return failed

    def validate(self, df: pd.DataFrame) -> typing.Collection[ValidationWarning]:
        """
        Validates a data frame
        :param df: Data frame to validate
        :return: All validation failures detected by this validation
        """
        # index = self.get_failed_index(df)
        # if self.negated:
        #     index = self.apply_negation(index)
        # failed = index(df)

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

    @abc.abstractmethod
    def prefix(self, warning: ValidationWarning):
        """
        Return a string that can be used to prefix a message that relates to this index

        This method is safe to override
        """

    def __or__(self, other: 'BaseValidation'):
        if not isinstance(other, BaseValidation):
            raise PanSchArgumentError('The "|" operator can only be used between two'
                                      'Validations that subclass {}'.format(
                self.__class__))

        return CombinedValidation(self, other, operator=operator.or_)

    def __and__(self, other: 'BaseValidation'):
        if not isinstance(other, BaseValidation):
            raise PanSchArgumentError('The "|" operator can only be used between two'
                                      'Validations that subclass {}'.format(
                self.__class__))

        return CombinedValidation(self, other, operator=operator.and_)

    def __invert__(self):
        """
        Return a copy of this, except that it will return indices of those that would normally pass this validation,
        in the same series
        """
        clone = copy.copy(self)
        clone.negated = True
        return clone


class IndexValidation(BaseValidation):
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

    def apply_index(self, df: pd.DataFrame):
        """
        Select a series using the data stored in this validation
        """
        return self.index(df)

    def prefix(self, warning: ValidationWarning):
        """
        Return a string that can be used to prefix a message that relates to this index

        This method is safe to override
        """
        ret = []

        if self.index.col_index is not None:
            col_str = self.index.col_index.for_message()
            if col_str:
                ret.append(col_str)

        ret.append('Row {}'.format(warning.props['row']))

        ret.append('"{}"'.format(warning.props['value']))

        return ' '.join(ret)

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        selection = self.apply_index(df)
        return self.validate_selection(selection)

    def get_failed_index(self, df) -> DualAxisIndexer:
        return self.get_passed_index(df).invert(axis=0)

        # Normally, validate_series returns the indices of the cells that passed the validation, but here we want the
        # cells that failed it, so invert the series (unless this is a negated validation)
        # if self.negated:
        #     row_index = selected
        # else:
        #     row_index = ~selected

        # Combine the index and the result series into one set of indexes
        # return DualAxisIndexer(
        #     row_index=row_index
        #     col_index=self.index.col_index
        # )

    @abc.abstractmethod
    def validate_selection(self, selection: SubSelection) -> DualAxisIndexer:
        """
        Given a series, return an indexer that
            passes the validation, otherwise False
        """
        pass

    def negate(self, axis: int):
        """
        Returns a copy of this validation, but with an inverted indexer
        """
        return self.__class__(index=self.index.invert(axis))


class SeriesValidation(IndexValidation):
    """
    A type of IndexValidation that operates only on a Series. This class mostly adds utility methods rather than
    any particular functionality.
    """

    def __init__(self, index, *args, **kwargs):
        super().__init__(
            *args,
            index=DualAxisIndexer(
                col_index=index,
                row_index=RowIndexer(index=slice(None), typ=IndexType.POSITION),
            ),
            **kwargs
        )

    def apply_negation(self, index: DualAxisIndexer) -> DualAxisIndexer:
        """
        When a SeriesValidation is negated, it means that we should invert only the row indices returned by the
        validation. This makes the validation return warnings from the same subset of the DataFrame, but makes cells
        pass if they would fail, and fail if they would pass
        """
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
        if isinstance(row_index, bool):
            if row_index:
                row_index = slice(None)
            else:
                row_index = []

        return DualAxisIndexer(
            row_index=row_index,
            col_index=self.index.col_index
        )

    @abc.abstractmethod
    def validate_series(self, series: pd.Series) -> IndexValue:
        """
        Given a series, return a bool Series that has values of True if the series
            passes the validation, otherwise False
        """


# class BooleanSeriesValidation(IndexValidation, WarningSeriesGenerator):
#     """
#     Validation is defined by the function :py:meth:~select_cells that returns a boolean series.
#         Each cell that has False has failed the validation.
#
#         Child classes need not create their own :py:class:~pandas_schema.core.BooleanSeriesValidation.Warning subclass,
#         because the data is in the same form for each cell. You need only define a :py:meth~default_message.
#     """
#
#     def __init__(self, *args, negated=False, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.negated = negated
#
#     @abc.abstractmethod
#     def select_cells(self, series: pd.Series) -> pd.Series:
#         """
#         A BooleanSeriesValidation must return a boolean series. Each cell that has False has failed the
#             validation
#         :param series: The series to validate
#         """
#         pass
#
#     def validate_series(self, series, flatten=True) -> typing.Union[
#         typing.Iterable[ValidationWarning],
#         pd.Series
#     ]:
#         """
#         Validates a single series selected from the DataFrame
#         """
#         selection = self.select_cells(series)
#
#         if self.negated:
#             # If self.negated (which is not the default), then we don't need to flip the booleans
#             failed = selection
#         else:
#             # In the normal case we do need to flip the booleans, since select_cells returns True for cells that pass
#             # the validation, and we want cells that failed it
#             failed = ~selection
#
#         # Slice out the failed items, then map each into a list of validation warnings at each respective index
#         warnings = series[failed].to_frame().apply(
#             lambda row: [ValidationWarning(self, {
#                 'row': row.name,
#                 'value': row[0]
#             })], axis='columns', result_type='reduce')
#         # warnings = warnings.iloc[:, 0]
#
#         # If flatten, return a list of ValidationWarning, otherwise return a series of lists of Validation Warnings
#         if flatten:
#             return self.flatten_warning_series(warnings)
#         else:
#             return warnings
#
#     def get_warning_series(self, df: pd.DataFrame) -> pd.Series:
#         """
#         Validates a series and returns a series of warnings.
#         """
#         series = self.select_series(df)
#         return self.validate_series(series, flatten=False)
#
#     def prefix(self, warning: ValidationWarning):
#         parent = super().prefix(warning)
#         # Only in this subclass do we know the contents of the warning props, since we defined them in the
#         # validate_series method. Thus, we can now add row index information
#
#         return parent + ', Row {row}: "{value}"'.format(**warning.props)
#
#     def __invert__(self) -> 'BooleanSeriesValidation':
#         """
#         If a BooleanSeriesValidation is negated, it has the opposite result
#         """
#         self.negated = not self.negated
#         return self


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
        super().__init__()
        self.operator = operator
        self.left = validation_a
        self.right = validation_b
        self.axis = axis

    def apply_negation(self, index: DualAxisIndexer) -> DualAxisIndexer:
        pass
    
    def combine_indices(self, left: DualAxisIndexer, right: DualAxisIndexer) -> DualAxisIndexer:
        """
        Utility method for combining the indexers using boolean logic
        :param left:
        :param right:
        :return:
        """
        # TODO: convert axis into an integer and apply proper panas logic
        if self.axis == 'rows':
            assert left.col_index == right.col_index
            assert isinstance(left.row_index.index, pd.Series)
            return DualAxisIndexer(
                row_index=self.operator(
                    left.row_index.index,
                    right.row_index.index
                ),
                col_index=left.col_index
            )

        elif self.axis == 'columns':
            assert left.row_index == right.row_index
            assert isinstance(left.col_index.index, pd.Series)
            return DualAxisIndexer(
                row_index=left.row_index,
                col_index=self.operator(
                    left.col_index.index,
                    right.col_index.index
                )
            )

        else:
            raise Exception()

    def get_passed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        left_passed = self.left.get_passed_index(df)
        right_passed = self.right.get_passed_index(df)
        return self.combine_indices(left_passed, right_passed)

    def get_failed_index(self, df: pd.DataFrame) -> DualAxisIndexer:
        return self.get_passed_index(df).invert(self.axis)

    def prefix(self, warning: ValidationWarning):
        pass

    def message(self, warning: ValidationWarning) -> str:
        pass

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

        # Convert the data into warnings, and then join together the warnings from both validations
        warnings = pd.concat([
            self.left.index_to_warnings_series(df, left_index, left_failed),
            self.right.index_to_warnings_series(df, right_index, right_failed)
        ])#, join='inner', keys=['inner', 'outer'])

        # Finally, apply the combined index from above to the warnings series
        if self.axis == 'rows':
            return warnings[combined.row_index.index]
        else:
            return warnings[combined.col_index.index]

    def default_message(self, warnings: ValidationWarning) -> str:
        return '({}) {} ({})'.format(self.v_a.message, self.operator, self.v_b.message)
