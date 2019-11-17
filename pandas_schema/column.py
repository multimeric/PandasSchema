import typing
import pandas as pd

from . import validation
from .validation_warning import ValidationWarning


def _column(
        validations: typing.Iterable[validation.IndexSeriesValidation],
        index: typing.Union[int, str] = None,
        position: bool = False
):
    """
    A utility method for setting the index data on a set of Validations
    :param validations: A list of validations to modify
    :param index: The index of the series that these validations will now consider
    :param position: If true, these validations use positional indexing.
    See :py:class:`pandas_schema.validation.IndexSeriesValidation`
    """
    for valid in validations:
        valid.index = index
        valid.position = position


def label_column(
        validations: typing.Iterable[validation.IndexSeriesValidation],
        index: typing.Union[int, str],
):
    """
    A utility method for setting the label-based column for each validation
    :param validations: A list of validations to modify
    :param index: The label of the series that these validations will now consider
    """
    return _column(
        validations,
        index,
        position=False
    )


def positional_column(
        validations: typing.Iterable[validation.IndexSeriesValidation],
        index: int,
):
    """
    A utility method for setting the position-based column for each validation
    :param validations: A list of validations to modify
    :param index: The index of the series that these validations will now consider
    """
    return _column(
        validations,
        index,
        position=True
    )
