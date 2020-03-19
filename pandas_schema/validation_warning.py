from dataclasses import dataclass, field


@dataclass
class ValidationWarning:
    """
    Represents a difference between the schema and data frame, found during the validation
    of the data frame
    """
    validation: 'pandas_schema.core.BaseValidation'
    """
    The validation that spawned this warning
    """

    props: dict = field(default_factory=dict)
    """
    List of data about this warning in addition to that provided by the validation, for
    example, if a cell in the DataFrame didn't match the validation, the props might
    include a `value` key, for storing what the actual value was
    """

    @property
    def message(self):
        """
        Return this validation as a string
        """
        # Internally, this actually asks the validator class to formulate a message
        return self.validation.message(self)

    def __str__(self):
        return self.message
