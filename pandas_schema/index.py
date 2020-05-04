from pandas_schema.errors import PanSchIndexError
from dataclasses import dataclass
from typing import Union, Optional, Any
import numpy as np
import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod, ABCMeta

# IndexError: only integers, slices (`:`), ellipsis (`...`), np.newaxis (`None`) and integer or boolean arrays are valid indices
IndexValue = Union[np.ndarray, pd.Series, str, int, slice]
"""
A pd index can either be an integer or string, or an array of either. This typing is a bit sketchy because really
a lot of things are accepted here
"""


class IndexType(Enum):
    POSITION = 0
    LABEL = 1

@dataclass
class AxisIndexer(ABC):
    """
    Abstract base class for indexers
        Each index represents a particular slice on a particular axis of a DataFrame. In this way, each AxisIndexer
        attempts to recreate the behaviour of `df.ix[some_index]`
    """

    index: Any
    """
    The index to use, either an integer for position-based indexing, or a string for label-based indexing
    """

    axis: int
    """
    The axis for the indexer
    """

    @abstractmethod
    def __call__(self, df: pd.DataFrame):
        """
        Apply this index
        :param df: The DataFrame to index
        :param axis: The axis to index along. axis=0 will select a row, and axis=1 will select a column
        """

    @abstractmethod
    def for_loc(self, df: pd.DataFrame):
        """
        Returns this index as something that could be passed into df.loc[]
        """

    @abstractmethod
    def for_iloc(self, df):
        """
        Returns this index as something that could be passed into df.iloc[]
        """

    @abstractmethod
    def for_message(self) -> Optional[str]:
        """
        Returns a string that could be used to describe this indexer in a human readable way. However, returns None
        if this indexer should not be described
        """

    @abstractmethod
    def __invert__(self) -> 'AxisIndexer':
        """
        Returns an index that is inverted (will return the opposite of what was previously specified)
        """


@dataclass(init=False)
class DirectIndexer(AxisIndexer):
    """
    A simple indexer that passes its index value directly into loc or iloc. For this reason it support any kind of
    indexing, using boolean series, label series, position series, slices etc
    """

    type: IndexType
    """
    The type of indexing to use, either 'position' or 'label'
    """

    negate: bool
    """
    If yes, return all values that this index does *not* select
    """
    # index: IndexValue
    """
    The index to use, either an integer for position-based indexing, or a string for label-based indexing
    """

    def __init__(self, index: IndexValue, typ: IndexType = None, axis: int = 1, negate=False):
        self.index = index
        self.axis = axis
        self.negate = negate

        if typ is not None:
            if not isinstance(typ, IndexType):
                raise PanSchIndexError('Index must be a subclass of IndexType')
            self.type = typ
        else:
            # If the type isn't provided, guess it based on the datatype of the index
            if isinstance(index, slice):
                # Slices can be used in either indexer
                self.type = IndexType.POSITION
            elif isinstance(index, list):
                self.type = IndexType.POSITION
            elif isinstance(index, pd.Series) and np.issubdtype(index.dtype, np.bool_):
                # Boolean series can actually be used in loc or iloc, but let's assume it's only iloc for simplicity
                self.type = IndexType.POSITION
            elif np.issubdtype(type(index), np.character):
                self.type = IndexType.LABEL
            elif np.issubdtype(type(index), np.int_):
                self.type = IndexType.POSITION
            else:
                raise PanSchIndexError('The index value was not either an integer or string, or an array of either of '
                                       'these')

    def __call__(self, df: pd.DataFrame):
        """
        Apply this index
        :param df: The DataFrame to index
        :param axis: The axis to index along. axis=0 will select a row, and axis=1 will select a column
        """
        if self.type == IndexType.LABEL:
            return df.loc(axis=self.axis)[self.index]
        elif self.type == IndexType.POSITION:
            return df.iloc(axis=self.axis)[self.index]

    def for_loc(self, df: pd.DataFrame):
        """
        Returns this index as something that could be passed into df.loc[]
        """
        if self.type == IndexType.LABEL:
            return self.index
        elif self.type == IndexType.POSITION:
            return df.axes[self.axis][self.index]

    def for_iloc(self, df):
        """
        Returns this index as something that could be passed into df.iloc[]
        """
        if self.type == IndexType.LABEL:
            return df.axes[self.axis].get_indexer(self.index)
        elif self.type == IndexType.POSITION:
            return self.index

    def for_message(self) -> Optional[str]:
        """
        Returns a string that could be used to describe this indexer in a human readable way. However, returns None
        if this indexer should not be described
        """
        if self.axis == 0:
            prefix = "Row"
        else:
            prefix = "Column"

        if isinstance(self.index, int):
            idx = str(self.index)
        elif isinstance(self.index, str):
            idx = '"{}"'.format(self.index)
        elif isinstance(self.index, slice):
            if self.index == slice(None):
                # If it's a slice of everything, skip this index
                return None
            else:
                idx = str(self.index)
        else:
            idx = str(self.index)

        return "{} {}".format(prefix, idx)

    @staticmethod
    def invert_index(index: IndexValue):
        if isinstance(index, slice) and index.start is None and index.stop is None:
            # If this is a None slice, it would previously return everything, so make it return nothing
            return []
        elif isinstance(index, list) and len(index) == 0:
            # If this is an empty list, it would previously return nothing, so make it return everything
            return slice(None)
        elif isinstance(index, pd.Series) and np.issubdtype(index.dtype, np.bool_):
            # Boolean series have a built-in inversion
            return ~index
        # elif np.issubdtype(type(index), np.int_):
        #     # Index series can't be inverted without knowing the original DF
        else:
            raise PanSchIndexError('Uninvertible type')

    def __invert__(self) -> 'AxisIndexer':
        """
        Returns an index that is inverted (will return the opposite of what was previously specified)
        """
        return DirectIndexer(
            # index=self.invert_index(self.index),
            index=self.index,
            typ=self.type,
            axis=self.axis,
            negate=not self.negate
        )

BooleanIndexType = Union[pd.Series, bool]


class BooleanIndexer(AxisIndexer):
    def __init__(self, index: BooleanIndexType, axis: int = 1):
        self.index = index
        self.axis = axis

    def __invert__(self) -> 'AxisIndexer':
        return BooleanIndexer(
            index=np.logical_not(self.index),
            axis=self.axis
        )

    @property
    def direct_index(self):
        """
        Converts this indexer's self.index into a value that can be passed directly into iloc[]
        """
        # If it's a scalar boolean, we need special values
        if np.issubdtype(type(self.index), np.bool_) and np.ndim(self.index) == 0:
            if self.index:
                return slice(None)
            else:
                return []

        # If it's a vector, pandas can deal with it
        return self.index

    def __call__(self, df: pd.DataFrame):
        """
        Apply this index
        :param df: The DataFrame to index
        :param axis: The axis to index along. axis=0 will select a row, and axis=1 will select a column
        """
        return df.iloc(axis=self.axis)[self.direct_index]

    def for_loc(self, df: pd.DataFrame):
        """
        Returns this index as something that could be passed into df.loc[]
        """
        return self.direct_index

    def for_iloc(self, df):
        """
        Returns this index as something that could be passed into df.iloc[]
        """
        return self.direct_index

    def for_message(self) -> Optional[str]:
        """
        Returns a string that could be used to describe this indexer in a human readable way. However, returns None
        if this indexer should not be described
        """
        if self.axis == 0:
            prefix = "Row"
        else:
            prefix = "Column"

        return "{} {}".format(prefix, str(self.index))


class SubIndexerMeta(ABCMeta):
    """
    Metaclass for RowIndexer and ColumnIndexer, allowing then to do instance checks in a more flexible way
    """
    def __init__(cls, *args, axis: int, **kwargs):
        super().__init__(*args)
        cls.axis = axis

    def __new__(metacls, name, bases, namespace, **kargs):
        return super().__new__(metacls, name, bases, namespace)

    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return super().__prepare__(name, bases, **kwargs)

    def __instancecheck__(self, instance):
        # Any AxisIndexer can be considered a ColumnIndexer if it has axis 0
        result = super().__instancecheck__(instance)
        if not result and isinstance(instance, AxisIndexer) and instance.axis == self.axis:
            return True
        else:
            return result


class RowIndexer(AxisIndexer, axis=0, metaclass=SubIndexerMeta):
    pass


class ColumnIndexer(AxisIndexer, axis=1, metaclass=SubIndexerMeta):
    pass


@dataclass(init=False)
class DualAxisIndexer:
    """
    Completely specifies some subset of a DataFrame, using both axes
    """
    row_index: RowIndexer
    col_index: ColumnIndexer

    def __init__(self, row_index: Union[RowIndexer, IndexValue], col_index: Union[ColumnIndexer, IndexValue]):
        # Use the validation and automatic conversion built into the AxisIndexer class to handle these inputs
        if isinstance(row_index, RowIndexer):
            self.row_index = row_index
        else:
            self.row_index = DirectIndexer(index=row_index, axis=0)

        if isinstance(col_index, ColumnIndexer):
            self.col_index = col_index
        else:
            self.col_index = DirectIndexer(index=col_index, axis=1)

    def __call__(self, df: pd.DataFrame):
        return df.loc[self.row_index.for_loc(df), self.col_index.for_loc(df)]

    def invert(self, axis) -> 'AxisIndexer':
        """
        Returns an index that is inverted along the given axis. e.g. if axis=0, the column index stays the same, but
        all row indices are inverted.
        """
        if axis == 0:
            return DualAxisIndexer(
                row_index=~self.row_index,
                col_index=self.col_index
            )

        elif axis == 1:
            return DualAxisIndexer(
                row_index=self.row_index,
                col_index=~self.col_index
            )
