import typing
from validation import Validation
import pandas as pd
from validation_error import ValidationError


class Column:
    def __init__(self, name: str, validations: typing.Iterable[Validation] = [], allow_empty=False):
        self.name = name
        self.validations = list(validations)
        self.allow_empty = allow_empty

    def validate(self, series: pd.Series) -> typing.List[ValidationError]:
        errors = []

        # Apply each validation one at a time
        for validation in self.validations:

            # Calculate which columns are valid based on the current validation, skipping empty entries
            simple_validation = ~validation.validate(series)
            if self.allow_empty:
                # Failing results are those that are not empty, and fail the validation
                validated = (series.str.len() > 0) & simple_validation
            else:
                validated = simple_validation

            # Cut down the original series to only ones that failed the validation
            indices = series.index[validated]

            # Use these indices to find the failing items. Also print the index which is probably a row number
            for i in indices:
                element = series[i]
                errors.append(ValidationError(
                    message=validation.get_message(element),
                    row=i,
                    column=series.name
                ))

        return errors
