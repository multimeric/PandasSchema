from pandas_schema.errors import PanSchIndexError
from dataclasses import dataclass
from typing import Union, Optional
import numpy
import pandas
from enum import Enum

IndexValue = Union[numpy.string_, numpy.int_, str, int, slice]
"""
A pandas index can either be an integer or string, or an array of either. This typing is a bit sketchy because really
a lot of things are accepted here
"""


class IndexType(Enum):
    POSITION = 0
    LABEL = 1


class AxisIndexer:
    """
    An index into a particular axis of a DataFrame. Attempts to recreate the behaviour of `df.ix[some_index]`
    """

    index: IndexValue
    """
    The index to use, either an integer for position-based indexing, or a string for label-based indexing
    """

    type: IndexType
    """
    The type of indexing to use, either 'position' or 'label'
    """

    axis: int
    """
    The axis for the indexer
    """

    def __init__(self, index: IndexValue, typ: IndexType = None, axis: int = 1):
        self.index = index
        self.axis = axis

        if typ is not None:
            if not isinstance(typ, IndexType):
                raise PanSchIndexError('Index must be a subclass of IndexType')
            self.type = typ
        else:
            # If the type isn't provided, guess it based on the datatype of the index
            if isinstance(index, pandas.Series) and numpy.issubdtype(index.dtype, numpy.bool_):
                # Boolean series can actually be used in loc or iloc, but let's assume it's only iloc for simplicity
                self.type = IndexType.POSITION
            elif numpy.issubdtype(type(index), numpy.character):
                self.type = IndexType.LABEL
            elif numpy.issubdtype(type(index), numpy.int_):
                self.type = IndexType.POSITION
            else:
                raise PanSchIndexError('The index value was not either an integer or string, or an array of either of '
                                       'these')

    def __call__(self, df: pandas.DataFrame):
        """
        Apply this index
        :param df: The DataFrame to index
        :param axis: The axis to index along. axis=0 will select a row, and axis=1 will select a column
        """
        if self.type == IndexType.LABEL:
            return df.loc(axis=self.axis)[self.index]
        elif self.type == IndexType.POSITION:
            return df.iloc(axis=self.axis)[self.index]

    def for_loc(self, df: pandas.DataFrame):
        """
        Returns this index as something that could be passed into df.loc[]
        """
        if self.type == IndexType.LABEL:
            return df.axes[self.axis][self.index]
        elif self.type == IndexType.POSITION:
            return self.index

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


class RowIndexer(AxisIndexer):
    def __init__(self, index: IndexValue, typ: IndexType = None):
        super().__init__(index=index, typ=typ, axis=0)


class ColumnIndexer(AxisIndexer):
    def __init__(self, index: IndexValue, typ: IndexType = None):
        super().__init__(index=index, typ=typ, axis=1)


@dataclass
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
            self.row_index = RowIndexer(index=row_index)

        if isinstance(col_index, ColumnIndexer):
            self.col_index = col_index
        else:
            self.col_index = ColumnIndexer(index=col_index)

    def __call__(self, df: pandas.DataFrame):
        return df.loc[self.row_index.for_loc(df), self.col_index.for_loc(df)]
