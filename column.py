import typing
from validation import Validation
import pandas as pd
from validation_error import ValidationError
import numpy as np

class Column:
    def __init__(self, name: str, validations: typing.Iterable[Validation] = [], allow_empty=False):
        self.name = name
        self.validations = list(validations)
        self.allow_empty = allow_empty

    def validate(self, series: pd.Series) -> typing.List[ValidationError]:
        errors = []

        for validation in self.validations:

            # Calculate which columns are valid based on the current validation, skipping empty entries
            if self.allow_empty:
                validated = series.isnull | validation.validate(series)
            else:
                validated = validation.validate(series)

            # Cut down the original series using that
            indicies = np.extract(validated, series)

            for row in indicies.itertuples():
                errors.append(ValidationError(
                    validation.get_message(getattr(row, self.name)),
                    getattr(row, rownum),
                    self.name
                ))


        return errors
