import typing

import pandas_schema.core
from pandas_schema.index import PandasIndexer


def column(
        validations: typing.Iterable['pandas_schema.core.IndexSeriesValidation'],
        index: PandasIndexer = None,
        override: bool = False
):
    """
    A utility method for setting the index data on a set of Validations
    :param validations: A list of validations to modify
    :param index: The index of the series that these validations will now consider
    :param override: If true, override existing index values. Otherwise keep the existing ones
    See :py:class:`pandas_schema.validation.IndexSeriesValidation`
    """
    for valid in validations:
        if override or valid.index is None:
            valid.index = index


def column_sequence(
        validations: typing.Iterable['pandas_schema.core.IndexSeriesValidation'],
        override: bool = False
):
    """
    A utility method for setting the index data on a set of Validations. Applies a sequential position based index, so
    that the first validation gets index 0, the second gets index 1 etc. Note: this will not modify any index that
    already has some kind of index
    :param validations: A list of validations to modify
    :param override: If true, override existing index values. Otherwise keep the existing ones
    """
    for i, valid in validations:
        if override or valid.index is None:
            valid.index = PandasIndexer(i, typ='positional')
#
# def label_column(
#         validations: typing.Iterable['pandas_schema.core.IndexSeriesValidation'],
#         index: typing.Union[int, str],
# ):
#     """
#     A utility method for setting the label-based column for each validation
#     :param validations: A list of validations to modify
#     :param index: The label of the series that these validations will now consider
#     """
#     return _column(
#         validations,
#         index,
#         position=False
#     )
#
# def positional_column(
#         validations: typing.Iterable['pandas_schema.core.IndexSeriesValidation'],
#         index: int,
# ):
#     """
#     A utility method for setting the position-based column for each validation
#     :param validations: A list of validations to modify
#     :param index: The index of the series that these validations will now consider
#     """
#     return _column(
#         validations,
#         index,
#         position=True

