import pandas as pd
import typing

from pandas_schema.core import BaseValidation
from pandas_schema.errors import PanSchArgumentError, PanSchInvalidSchemaError
from pandas_schema.validation_warning import ValidationWarning
from pandas_schema.index import PandasIndexer


class Schema:
    """
    A schema that defines the columns required in the target DataFrame
    """

    def __init__(self, validations: typing.Iterable[BaseValidation]):
        """
        :param validations: A list of validations that will be applied to the DataFrame upon validation
        """
        if not validations:
            raise PanSchInvalidSchemaError('An instance of the schema class must have a validations list')

        if not isinstance(validations, typing.Iterable):
            raise PanSchInvalidSchemaError('The columns field must be an iterable of Validation objects')

        self.validations = list(validations)

    def validate(self, df: pd.DataFrame, subset: PandasIndexer = None) -> typing.List[ValidationWarning]:
        """
        Runs a full validation of the target DataFrame using the internal columns list

        :param df: A pandas DataFrame to validate
        :param subset: A list of columns indicating a subset of the schema that we want to validate. Can be any
        :return: A list of ValidationWarning objects that list the ways in which the DataFrame was invalid
        """
        # Apply the subset if we have one
        if subset is not None:
            df = subset(df)

        # Build the list of errors
        errors = []
        for validation in self.validations:
            errors.extend(validation.validate(df))
        return errors
