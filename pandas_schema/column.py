from typing import Union, Iterable

from pandas_schema.core import IndexValidation, BaseValidation
from pandas_schema.index import AxisIndexer, IndexValue


def column(
        validations: Union[Iterable['IndexValidation'], 'IndexValidation'],
        index = None,
        override: bool = False,
        recurse: bool = True,
        allow_empty: bool = False
) -> Union[Iterable['IndexValidation'], 'IndexValidation']:
    """A utility method for setting the index data on a set of Validations

    Args:
      validations: A list of validations to modify
      index: The index of the series that these validations will now consider
      override: If true, override existing index values. Otherwise keep the existing ones
      recurse: If true, recurse into child validations
      allow_empty: Allow empty rows (NaN) to pass the validation
    See :py:class:`pandas_schema.validation.IndexSeriesValidation` (Default value = False)
    Returns:
    """
    # TODO: Abolish this, and instead propagate the individual validator indexes when we And/Or them together
    def update_validation(validation: BaseValidation):
        if isinstance(validation, IndexValidation):
            if override or validation.index is None:
                validation.index = index

        if allow_empty:
            return validation.optional()
        else:
            return validation

    if isinstance(validations, Iterable):
        ret = []
        for valid in validations:
            if recurse:
                ret.append(valid.map(update_validation))
            else:
                ret.append(update_validation(valid))
        return ret
    else:
        if recurse:
            return validations.map(update_validation)
        else:
            return update_validation(validations)

    return validations


def column_sequence(
        validations: Iterable['IndexValidation'],
        override: bool = False
) -> Iterable['IndexValidation']:
    """A utility method for setting the index data on a set of Validations. Applies a sequential position based index, so
    that the first validation gets index 0, the second gets index 1 etc. Note: this will not modify any index that
    already has some kind of index unless you set override=True

    Args:
      validations: A list of validations to modify
      override: If true, override existing index values. Otherwise keep the existing ones
      validations: typing.Iterable['pandas_schema.core.IndexValidation']: 
      override: bool:  (Default value = False)

    Returns:

    """
    for i, valid in validations:
        if override or valid.index is None:
            valid.index = AxisIndexer(i, typ='positional')
    return validations


def each_column(validations: Iterable[IndexValidation], columns: IndexValue):
    """Duplicates a validation and applies it to each column specified

    Args:
      validations: A list of validations to apply to each column
      columns: An index that should, when applied to the column index, should return all columns you want this to
      validations: typing.Iterable[pandas_schema.core.IndexValidation]: 
      columns: IndexValue: 

    Returns:

    """

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
